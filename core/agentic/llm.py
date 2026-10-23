# -*- coding: utf-8 -*-
"""Pluggable LLM clients for the native agent (Ollama / OpenAI-compatible / scripted)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

import httpx

from core.api.control.tools import list_tools


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ChatResult:
    content: str = ''
    tool_calls: List[ToolCall] = field(default_factory=list)
    raw: Any = None


class LLMClient(Protocol):
    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> ChatResult:
        ...


def tools_openai_schema(descriptors: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Convert Control tool descriptors to OpenAI / Ollama function-tools."""
    out: List[Dict[str, Any]] = []
    for d in descriptors or list_tools():
        out.append({
            'type': 'function',
            'function': {
                'name': d['name'],
                'description': d.get('description') or '',
                'parameters': d.get('inputSchema') or {'type': 'object', 'properties': {}},
            },
        })
    return out


def _parse_args(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {'_raw': raw}
    return {}


class AgentLLMError(RuntimeError):
    """Raised when the LLM endpoint rejects the request (e.g. missing model)."""


PREFERRED_OLLAMA_MODELS = (
    'qwen3.5:0.8b',
    'qwen3.5',
    'qwen2.5-coder:7b',
    'llama3.2',
    'llama3.1',
)


def list_ollama_models(base_url: str = 'http://127.0.0.1:11434') -> List[str]:
    """Return installed Ollama model names (best-effort)."""
    root = (base_url or 'http://127.0.0.1:11434').rstrip('/')
    if root.endswith('/v1'):
        root = root[:-3]
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f'{root}/api/tags')
            if resp.status_code != 200:
                return []
            data = resp.json()
    except Exception:
        return []
    names: List[str] = []
    for m in data.get('models') or []:
        name = m.get('name') or m.get('model')
        if name:
            names.append(str(name))
    return names


def resolve_ollama_model(
    requested: Optional[str] = None,
    *,
    base_url: Optional[str] = None,
) -> str:
    """
    Pick a usable Ollama model.
    Prefer explicit request when installed; else preferred list; else first tag.
    """
    installed = list_ollama_models(base_url or 'http://127.0.0.1:11434')
    req = (requested or '').strip()
    if req and req.lower() not in ('auto', 'default'):
        if not installed or req in installed:
            return req
        for i in installed:
            if i.startswith(req + ':') or i.split(':')[0] == req.split(':')[0]:
                return i
        return req

    for pref in PREFERRED_OLLAMA_MODELS:
        for i in installed:
            if i == pref or i.startswith(pref + ':'):
                return i
        # bare family match e.g. pref qwen3.5 matches qwen3.5:0.8b
        family = pref.split(':')[0]
        for i in installed:
            if i.split(':')[0] == family:
                return i

    if installed:
        return installed[0]
    return 'llama3.2'


def _format_http_error(resp: httpx.Response, model: str, endpoint: str) -> str:
    body = ''
    try:
        body = resp.text[:500]
    except Exception:
        body = ''
    hint = ''
    if resp.status_code == 404:
        available = list_ollama_models()
        if available:
            hint = (
                f" Model {model!r} not found. Installed: {', '.join(available)}. "
                f"Pass --model <name> or set VIMANA_AGENT_MODEL."
            )
        else:
            hint = (
                f" Model {model!r} not found (and could not list Ollama tags). "
                f"Pass --model <name> or set VIMANA_AGENT_MODEL."
            )
    return f'LLM HTTP {resp.status_code} at {endpoint}:{hint} {body}'.strip()


class OpenAICompatClient:
    """Chat Completions API (Ollama `/v1`, LM Studio, cloud OpenAI-compatible)."""

    def __init__(
        self,
        base_url: str = 'http://127.0.0.1:11434/v1',
        model: str = 'llama3.2',
        api_key: str = 'ollama',
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> ChatResult:
        payload: Dict[str, Any] = {
            'model': self.model,
            'messages': messages,
            'stream': False,
        }
        if tools:
            payload['tools'] = tools
            payload['tool_choice'] = 'auto'

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        endpoint = f'{self.base_url}/chat/completions'
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(endpoint, headers=headers, json=payload)
            if resp.status_code >= 400:
                raise AgentLLMError(_format_http_error(resp, self.model, endpoint))
            data = resp.json()

        choice = (data.get('choices') or [{}])[0]
        message = choice.get('message') or {}
        content = message.get('content') or ''
        calls: List[ToolCall] = []
        for tc in message.get('tool_calls') or []:
            fn = tc.get('function') or {}
            calls.append(ToolCall(
                id=str(tc.get('id') or uuid.uuid4()),
                name=str(fn.get('name') or ''),
                arguments=_parse_args(fn.get('arguments')),
            ))
        return ChatResult(content=content, tool_calls=calls, raw=data)


class OllamaNativeClient:
    """Ollama native `/api/chat` (tools supported on recent builds)."""

    def __init__(
        self,
        base_url: str = 'http://127.0.0.1:11434',
        model: str = 'llama3.2',
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> ChatResult:
        ollama_tools = [t.get('function') or t for t in tools]
        payload: Dict[str, Any] = {
            'model': self.model,
            'messages': messages,
            'stream': False,
            'tools': ollama_tools,
        }
        endpoint = f'{self.base_url}/api/chat'
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(endpoint, json=payload)
            if resp.status_code >= 400:
                raise AgentLLMError(_format_http_error(resp, self.model, endpoint))
            data = resp.json()

        message = data.get('message') or {}
        content = message.get('content') or ''
        calls: List[ToolCall] = []
        for tc in message.get('tool_calls') or []:
            fn = tc.get('function') or tc
            calls.append(ToolCall(
                id=str(uuid.uuid4()),
                name=str(fn.get('name') or ''),
                arguments=_parse_args(fn.get('arguments')),
            ))
        return ChatResult(content=content, tool_calls=calls, raw=data)


def _last_tool_payload(messages: List[Dict[str, Any]]) -> Any:
    """Parse the most recent tool-role message content (JSON if possible)."""
    for msg in reversed(messages or []):
        if msg.get('role') != 'tool':
            continue
        content = msg.get('content')
        if isinstance(content, (dict, list)):
            return content
        if isinstance(content, str):
            text = content.strip()
            if not text:
                return {}
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {'_raw': text}
        return content
    return {}


def _resolve_last_refs(obj: Any, last: Any) -> Any:
    """Replace '$last.a.b' strings with values from the prior tool payload."""
    if isinstance(obj, str) and obj.startswith('$last'):
        if obj == '$last':
            return last
        if not obj.startswith('$last.'):
            return obj
        cur: Any = last
        for part in obj[6:].split('.'):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return obj
        return cur
    if isinstance(obj, dict):
        return {k: _resolve_last_refs(v, last) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_last_refs(v, last) for v in obj]
    return obj


class ScriptedClient:
    """Deterministic client for CI / smoke without a live model.

    Script: list of steps. Each step is either
      {"tool": "name", "arguments": {...}}
    or {"content": "final answer"} (ends the loop).

    Arguments may use ``$last.field`` (and nested paths) resolved from the
    previous tool result in the conversation — needed for e2e chaining
    (lab url → run → findings run_id).
    """

    def __init__(self, script: Optional[List[Dict[str, Any]]] = None) -> None:
        self.script = list(script or [
            {'tool': 'vimana_health', 'arguments': {}},
            {'tool': 'vimana_list_plugins', 'arguments': {}},
            {'content': 'Smoke complete: health checked and plugins listed.'},
        ])
        self._i = 0

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> ChatResult:
        del tools
        if self._i >= len(self.script):
            return ChatResult(content='(script exhausted)')
        step = self.script[self._i]
        self._i += 1
        if 'tool' in step:
            last = _last_tool_payload(messages)
            arguments = _resolve_last_refs(dict(step.get('arguments') or {}), last)
            return ChatResult(
                content='',
                tool_calls=[ToolCall(
                    id=f'script-{self._i}',
                    name=str(step['tool']),
                    arguments=arguments if isinstance(arguments, dict) else {},
                )],
            )
        return ChatResult(content=str(step.get('content') or ''))

def build_client(
    provider: str,
    *,
    model: str = '',
    base_url: Optional[str] = None,
    api_key: str = 'ollama',
) -> LLMClient:
    name = (provider or 'ollama').strip().lower()
    if name == 'scripted':
        return ScriptedClient()

    resolved = (model or '').strip()
    if name in ('ollama', 'ollama_native') and not resolved:
        resolved = resolve_ollama_model('auto', base_url=base_url)
    if not resolved and name in ('openai', 'openai_compat', 'lmstudio', 'v1'):
        resolved = 'llama3.2'

    if name in ('openai', 'openai_compat', 'lmstudio', 'v1'):
        return OpenAICompatClient(
            base_url=base_url or 'http://127.0.0.1:11434/v1',
            model=resolved,
            api_key=api_key,
        )
    if name == 'ollama':
        return OpenAICompatClient(
            base_url=base_url or 'http://127.0.0.1:11434/v1',
            model=resolved,
            api_key=api_key,
        )
    if name == 'ollama_native':
        return OllamaNativeClient(
            base_url=base_url or 'http://127.0.0.1:11434',
            model=resolved,
        )
    raise ValueError(f'unknown LLM provider: {provider}')
