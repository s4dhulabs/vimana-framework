# -*- coding: utf-8 -*-
# GraphQL security probes for schemage.

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import requests
from neotermcolor import colored

from core.vmnf_channels import register_channel
from core.findings import Finding as GqlFinding
from siddhis.schemage.utils import get_hash, join_url, parse_auth_header


INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    types { name kind }
  }
}
"""


# Default CWE tags by check id (flows into JSON + SARIF)
_CHECK_CWE = {
    'introspection_enabled': 'CWE-200',
    'unbounded_query_depth': 'CWE-400',
    'alias_batch_overload': 'CWE-400',
    'cross_tenant_order_idor': 'CWE-639',
    'cross_tenant_mutation_idor': 'CWE-639',
    'unauthenticated_sensitive_query': 'CWE-306',
}


class GraphQLAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.timeout = float(handler.get('timeout') or 15)
        self.verbose = bool(handler.get('verbose'))
        self.path = str(handler.get('gql_path') or '/graphql/')
        if self.path != '/' and not self.path.endswith('/'):
            # Starlette often 307-redirects /graphql → /graphql/
            self.path = self.path + '/'
        self.auth_a = handler.get('gql_auth_a') or 'Bearer user-a-token'
        self.auth_b = handler.get('gql_auth_b') or 'Bearer user-b-token'
        self.max_depth = int(handler.get('gql_max_depth') or 8)
        self.checks_mode = (handler.get('gql_checks') or 'all').lower()
        self.order_a = str(handler.get('gql_order_a') or '1')
        self.order_b = str(handler.get('gql_order_b') or '2')

    def _post(
        self,
        url: str,
        query: str,
        variables: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Tuple[Optional[dict], Optional[int], Optional[str]]:
        try:
            resp = requests.post(
                url,
                json={'query': query, 'variables': variables or {}},
                headers=headers or {'Content-Type': 'application/json'},
                timeout=self.timeout,
                allow_redirects=True,
            )
            try:
                data = resp.json()
            except Exception:
                data = {'raw': resp.text[:500]}
            return data, resp.status_code, None
        except Exception as exc:
            return None, None, str(exc)

    def audit(self, base_url: str) -> List[GqlFinding]:
        findings: List[GqlFinding] = []
        url = join_url(base_url, self.path)
        mode = self.checks_mode
        headers_a = parse_auth_header(self.auth_a)
        headers_a['Content-Type'] = 'application/json'
        headers_b = parse_auth_header(self.auth_b)
        headers_b['Content-Type'] = 'application/json'

        # 1) Introspection
        if mode in ('all', 'introspection'):
            data, status, err = self._post(url, INTROSPECTION_QUERY)
            schema = (data or {}).get('data', {}).get('__schema') if data else None
            if schema:
                type_names = [t.get('name') for t in schema.get('types') or [] if t.get('name')]
                findings.append(GqlFinding(
                    target=url,
                    check='introspection_enabled',
                    severity='medium',
                    detail=(
                        f'GraphQL introspection is enabled at {self.path} '
                        f'(HTTP {status}). Schema types leaked: {len(type_names)}.'
                    ),
                    evidence={
                        'status': status,
                        'type_count': len(type_names),
                        'sample_types': type_names[:15],
                    },
                ))
            elif self.verbose:
                print(colored(f'  [ok] introspection blocked: {err or status}', 'green'))

        # 2) Depth / nested overload
        if mode in ('all', 'depth'):
            # Build nested selection on Order.owner.orders.owner... if schema supports;
            # fallback: deeply nested alias spam on order(id)
            depth = max(3, self.max_depth)
            nested = 'id'
            for _ in range(depth):
                nested = f'owner {{ username orders {{ {nested} }} }}'
            query = f'query {{ order(id: "{self.order_a}") {{ {nested} }} }}'
            data, status, err = self._post(url, query, headers=headers_a)
            # If no GraphQL errors about depth AND data returned → weak depth limit
            errors = (data or {}).get('errors') or []
            depth_blocked = any(
                'depth' in str(e).lower() or 'complexity' in str(e).lower()
                for e in errors
            )
            if data and data.get('data') is not None and not depth_blocked and status and 200 <= status < 300:
                findings.append(GqlFinding(
                    target=url,
                    check='unbounded_query_depth',
                    severity='medium',
                    detail=(
                        f'Deeply nested query (depth≈{depth}) was accepted without '
                        'depth/complexity rejection.'
                    ),
                    evidence={'status': status, 'depth': depth, 'errors': errors[:3]},
                ))
            # Alias batching
            aliases = ' '.join(
                f'a{i}: order(id: "{self.order_a}") {{ id secret }}' for i in range(25)
            )
            batch_q = f'query {{ {aliases} }}'
            data2, status2, _ = self._post(url, batch_q, headers=headers_a)
            if data2 and data2.get('data') and status2 and 200 <= status2 < 300:
                keys = list((data2.get('data') or {}).keys())
                if len(keys) >= 20:
                    findings.append(GqlFinding(
                        target=url,
                        check='alias_batch_overload',
                        severity='low',
                        detail=(
                            f'Alias batching accepted ({len(keys)} aliases). '
                            'Consider query cost limits.'
                        ),
                        evidence={'alias_count': len(keys), 'status': status2},
                    ))

        # 3) Cross-tenant order IDOR
        if mode in ('all', 'idor', 'authz'):
            q = 'query($id: ID!) { order(id: $id) { id owner { username } secret note amount } }'
            data, status, err = self._post(
                url, q, variables={'id': self.order_b}, headers=headers_a,
            )
            order = ((data or {}).get('data') or {}).get('order')
            if order and order.get('secret'):
                owner = (order.get('owner') or {}).get('username')
                findings.append(GqlFinding(
                    target=url,
                    check='cross_tenant_order_idor',
                    severity='high',
                    detail=(
                        f'Identity A ({self.auth_a!r}) read order {self.order_b!r} '
                        f'(owner={owner!r}, secret present). Possible field/object IDOR.'
                    ),
                    evidence={
                        'status': status,
                        'order': order,
                        'auth': self.auth_a,
                        'expected_order': self.order_a,
                    },
                ))
            elif self.verbose:
                print(colored(f'  [ok] order IDOR blocked: {err or status}', 'green'))

            # mutation IDOR
            mq = '''
            mutation($id: ID!, $note: String!) {
              updateOrderNote(id: $id, note: $note) { id note secret owner { username } }
            }
            '''
            data_m, status_m, _ = self._post(
                url,
                mq,
                variables={'id': self.order_b, 'note': 'schemage-probe'},
                headers=headers_a,
            )
            updated = ((data_m or {}).get('data') or {}).get('updateOrderNote')
            if updated and updated.get('id'):
                findings.append(GqlFinding(
                    target=url,
                    check='cross_tenant_mutation_idor',
                    severity='high',
                    detail=(
                        f'Identity A mutated order {self.order_b!r} via updateOrderNote. '
                        'Missing object-level authz on mutation.'
                    ),
                    evidence={'status': status_m, 'result': updated, 'auth': self.auth_a},
                ))

        # 4) Unauthenticated sensitive query
        if mode in ('all', 'unauth'):
            q = f'{{ order(id: "{self.order_a}") {{ id secret }} }}'
            data, status, _ = self._post(url, q)
            order = ((data or {}).get('data') or {}).get('order')
            if order and order.get('secret'):
                findings.append(GqlFinding(
                    target=url,
                    check='unauthenticated_sensitive_query',
                    severity='high',
                    detail=(
                        f'Unauthenticated query returned order secret for id={self.order_a}.'
                    ),
                    evidence={'status': status, 'order': order},
                ))

        for finding in findings:
            if not finding.cwe:
                finding.cwe = _CHECK_CWE.get(finding.check)
            if not finding.endpoint:
                finding.endpoint = self.path
            if not finding.method:
                finding.method = 'POST'
        return findings
        for f in findings:
            color = {'high': 'red', 'medium': 'yellow', 'low': 'white', 'info': 'blue'}.get(f.severity, 'white')
            print(colored(f'  [{f.severity.upper()}] {f.check}', color))
            print(f'      {f.detail}')
            print(f'      target: {f.target}')

    def register_channels(self, findings: List[GqlFinding], base_url: str) -> None:
        for f in findings:
            if f.severity not in ('high', 'medium'):
                continue
            channel_id = 'sg' + get_hash(f.target + f.check)[:6]
            register_channel({
                'channel_id': channel_id,
                'type': 'GraphQL',
                'plugin': 'schemage',
                'target_url': base_url,
                'endpoint': f.target,
                'method': 'POST',
                'payload_template': json.dumps({'check': f.check, 'detail': f.detail}),
                'description': f.detail,
                'status': 'active',
                'metadata': {'severity': f.severity, 'evidence': f.evidence},
            }, handler=self.handler)
