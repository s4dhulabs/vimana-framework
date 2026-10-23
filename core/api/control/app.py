# -*- coding: utf-8 -*-
"""FastAPI application — Framework Control API v1 + Admin UI static."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from core.api.control import services
from core.api.control.runs import RUN_STORE
from core.api.control.schemas import RunRequest

ADMIN_DIR = os.path.join(os.path.dirname(__file__), 'admin_ui')


def create_app() -> FastAPI:
    app = FastAPI(
        title='Vimana Control API',
        description='Operate Vimana Framework over HTTP (plugins, runs, labs, findings). '
                    'Distinct from the Exception Monitor API (core/api/backend).',
        version='1.0.0',
        docs_url='/docs',
        redoc_url='/redoc',
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            'http://127.0.0.1',
            'http://localhost',
            'http://127.0.0.1:8090',
            'http://localhost:8090',
            'http://127.0.0.1:3000',
            'http://localhost:3000',
            'http://127.0.0.1:8000',
            'http://localhost:8000',
            'null',  # file:// admin during local open
        ],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    @app.get('/')
    def root():
        return RedirectResponse(url='/admin/')

    @app.get('/v1/health')
    def v1_health():
        return services.health()

    @app.get('/v1/about')
    def v1_about():
        """Framework overview (same payload as tool vimana_about / CLI spirit)."""
        return services.about()

    @app.post('/v1/analyze')
    def v1_analyze(body: Optional[Dict[str, Any]] = Body(None)):
        """
        Fingerprint a live target + triage catalog plugins
        (tool vimana_analyze_target / agent analyze playbook).
        """
        from core.api.control.analyze import analyze_target

        payload = body if isinstance(body, dict) else {}
        url = payload.get('target_url') or payload.get('url')
        if not url:
            raise HTTPException(status_code=400, detail='target_url required')
        try:
            return analyze_target(
                str(url),
                fingerprint_plugin=str(payload.get('fingerprint_plugin') or 'framewalk'),
                follow_up=bool(payload.get('follow_up') or False),
                follow_up_limit=int(payload.get('follow_up_limit') or 2),
                include_fuzzers=bool(payload.get('include_fuzzers') or False),
                auto=bool(payload.get('auto') or False),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f'{type(exc).__name__}: {exc}',
            ) from exc

    @app.get('/v1/tools')
    def v1_list_tools():
        """JSON tool descriptors for agents (MCP-compatible schema)."""
        from core.api.control.tools import list_tools
        return {
            'tools': list_tools(),
            'transport': {
                'mcp_stdio': 'vimana mcp',
                'http_invoke': 'POST /v1/tools/{name}',
            },
        }

    @app.get('/v1/mcp/connect')
    def v1_mcp_connect():
        """Cursor-ready MCP connect snippet (absolute paths for this install)."""
        from core.api.control.mcp_connect import mcp_connect_payload
        return mcp_connect_payload()

    @app.post('/v1/tools/{name}')
    def v1_call_tool(name: str, body: Optional[Dict[str, Any]] = Body(None)):
        """Invoke a Control tool in-process (same handlers as MCP)."""
        from core.api.control.tools import call_tool, get_tool
        if not get_tool(name):
            raise HTTPException(status_code=404, detail=f'unknown tool: {name}')
        arguments: Dict[str, Any] = {}
        if isinstance(body, dict):
            if 'arguments' in body and isinstance(body['arguments'], dict):
                arguments = body['arguments']
            else:
                arguments = {k: v for k, v in body.items() if k != 'arguments'}
        try:
            result = call_tool(name, arguments)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f'{type(exc).__name__}: {exc}') from exc
        return {'tool': name, 'result': result}

    @app.get('/v1/plugins')
    def v1_list_plugins():
        return {'plugins': services.list_plugins()}

    @app.get('/v1/plugins/{name}')
    def v1_get_plugin(name: str):
        detail = services.get_plugin(name)
        if not detail:
            raise HTTPException(status_code=404, detail=f'plugin not found: {name}')
        return detail

    @app.get('/v1/plugins/{name}/explain')
    def v1_explain_plugin(
        name: str,
        focus: str = Query('overview', description='overview | usage | args'),
    ):
        """Curated plugin guide card (tool vimana_explain_plugin)."""
        try:
            return services.explain_plugin(name, focus=focus)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post('/v1/plugins/{name}/run')
    def v1_run_plugin(
        name: str,
        body: Optional[RunRequest] = None,
        async_q: bool = Query(False, alias='async'),
    ):
        args: Dict[str, Any] = {}
        async_job = bool(async_q)
        if body:
            args.update(body.args or {})
            if getattr(body, 'async_mode', False):
                async_job = True
            # allow top-level extras as args too (pydantic v1/v2) — skip async flag
            if hasattr(body, 'model_dump'):
                extra = body.model_dump(exclude={'args', 'async_mode'}, exclude_unset=True)
            else:
                extra = body.dict(exclude={'args', 'async_mode'}, exclude_unset=True)
            extra.pop('async', None)
            args.update(extra)
        try:
            run = services.run_plugin(name, args, async_job=async_job)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if not run:
            raise HTTPException(status_code=500, detail='run store failure')
        payload = run.to_dict(include_report=not async_job)
        if async_job:
            return JSONResponse(status_code=202, content=payload)
        return payload

    @app.get('/v1/runs')
    def v1_list_runs(limit: int = Query(50, ge=1, le=200)):
        runs = RUN_STORE.list(limit=limit)
        return {
            'runs': [r.to_dict(include_report=False) for r in runs],
        }

    @app.get('/v1/runs/{run_id}')
    def v1_get_run(run_id: str):
        run = RUN_STORE.get(run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f'run not found: {run_id}')
        return run.to_dict(include_report=True)

    @app.get('/v1/findings/runs/{run_id}')
    def v1_findings(run_id: str):
        run = RUN_STORE.get(run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f'run not found: {run_id}')
        report = run.report or {}
        findings = report.get('findings')
        if findings is None and isinstance(report.get('summary'), dict):
            findings = report.get('summary', {}).get('findings')
        return {
            'run_id': run_id,
            'plugin': run.plugin,
            'status': run.status,
            'findings': findings if findings is not None else [],
            'summary': report.get('summary'),
            'report': report,
        }

    @app.get('/v1/labs')
    def v1_list_labs():
        return {'labs': services.list_labs()}

    @app.post('/v1/labs/cleanup')
    def v1_labs_cleanup():
        return services.lab_cleanup()

    @app.get('/v1/labs/{plugin}')
    def v1_lab_status(plugin: str):
        return services.lab_status(plugin)

    @app.post('/v1/labs/{plugin}/start')
    def v1_lab_start(plugin: str):
        return services.lab_start(plugin)

    @app.post('/v1/labs/{plugin}/stop')
    def v1_lab_stop(plugin: str):
        return services.lab_stop(plugin)

    @app.post('/v1/labs/{plugin}/test')
    def v1_lab_test(plugin: str):
        """Start lab if needed, then run plugin against it (CLI: --lab X --test)."""
        return services.lab_test(plugin)

    # --- Shared framework resources (OpenAPI specs, channels) ---
    @app.get('/v1/specs')
    def v1_list_specs():
        from core.api.control import resources as res
        return {'specs': res.list_specs()}

    @app.get('/v1/specs/{spec_id}')
    def v1_get_spec(spec_id: str):
        from core.api.control import resources as res
        detail = res.get_spec(spec_id, include_body=True)
        if not detail:
            raise HTTPException(status_code=404, detail=f'spec not found: {spec_id}')
        return detail

    @app.get('/v1/channels')
    def v1_list_channels(
        plugin: Optional[str] = Query(None),
        channel_type: Optional[str] = Query(None, alias='type'),
        status: Optional[str] = Query(None),
    ):
        from core.api.control import resources as res
        return {
            'channels': res.list_channels(
                plugin=plugin, channel_type=channel_type, status=status,
            ),
        }

    @app.get('/v1/channels/{channel_id}')
    def v1_get_channel(channel_id: str):
        from core.api.control import resources as res
        detail = res.get_channel(channel_id)
        if not detail:
            raise HTTPException(status_code=404, detail=f'channel not found: {channel_id}')
        return detail

    @app.get('/v1/resources/spec-consumers')
    def v1_spec_consumers():
        from core.api.control import resources as res
        return res.spec_consumers()

    @app.get('/v1/cases')
    def v1_list_cases():
        from core.api.control import resources as res
        return {'cases': res.list_cases()}

    @app.get('/v1/cases/{case_id}')
    def v1_get_case(case_id: str):
        from core.api.control import resources as res
        detail = res.get_case(case_id)
        if not detail:
            raise HTTPException(status_code=404, detail=f'case not found: {case_id}')
        return detail

    @app.post('/v1/cases/{case_id}/run')
    def v1_run_case(
        case_id: str,
        async_q: bool = Query(True, alias='async'),
    ):
        from core.api.control import resources as res
        try:
            run = res.run_case(case_id, async_job=bool(async_q))
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        payload = run.to_dict(include_report=not async_q)
        if async_q:
            return JSONResponse(status_code=202, content=payload)
        return payload

    # --- Atma: dogfood Control API with curated FastAPI suite ---
    @app.get('/v1/atma')
    def v1_atma_manifest():
        from core.api.control import atma as atma_mod
        return atma_mod.suite_manifest()

    @app.get('/v1/atma/active')
    def v1_atma_active():
        from core.api.control import atma as atma_mod
        job = atma_mod.ATMA_STORE.active()
        return {'job': job.to_dict() if job else None}

    @app.post('/v1/atma/start')
    def v1_atma_start(request: Request):
        from core.api.control import atma as atma_mod
        # Always dogfood loopback — ignore client Host (LAN / proxy) for safety.
        port = request.url.port or 8090
        base = f'http://127.0.0.1:{port}'
        try:
            job = atma_mod.start_atma(base)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return job.to_dict()

    @app.get('/v1/atma/{job_id}')
    def v1_atma_job(job_id: str):
        from core.api.control import atma as atma_mod
        job = atma_mod.ATMA_STORE.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f'atma job not found: {job_id}')
        return job.to_dict()

    # Exception Monitor (same process) — Admin Monitor drawer defaults here
    try:
        from core.api.backend.vf_server import DashboardServer
        monitor_server = DashboardServer()
        app.state.exception_monitor = monitor_server
        app.mount('/monitor', monitor_server.app)

        @app.get('/v1/monitor/info')
        def v1_monitor_info():
            return {
                'mounted': True,
                'base_path': '/monitor',
                'url_hint': '/monitor',
                'seed': 'POST /monitor/demo/seed?reset=true',
                'standalone_cli': 'vimana monitor --seed-demo',
                'dashboard_ui': 'http://127.0.0.1:3000',
            }
    except Exception as mon_exc:
        @app.get('/v1/monitor/info')
        def v1_monitor_info_unavailable():
            return {
                'mounted': False,
                'error': str(mon_exc),
                'standalone_cli': 'vimana monitor --seed-demo',
            }

    # Admin UI (static) — served under /admin
    if os.path.isdir(ADMIN_DIR):
        @app.get('/admin')
        def admin_redirect():
            return RedirectResponse(url='/admin/')

        @app.get('/admin/')
        def admin_index():
            index = os.path.join(ADMIN_DIR, 'index.html')
            return FileResponse(index)

        app.mount(
            '/admin/static',
            StaticFiles(directory=ADMIN_DIR),
            name='admin_static',
        )

    return app


# module-level app for `uvicorn core.api.control.app:app`
app = create_app()
