

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


from core.analyzers.django.django_analyzer import (
    DjangoExceptionAnalyzer, 
    SecurityFinding, 
    SecurityIssueType
)

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import socket
import json
import argparse
from datetime import datetime
import asyncio
from enum import Enum


class ExceptionSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CodeReassemblyRequest(BaseModel):
    """Request model for code reassembly"""
    exceptions: List[Dict[str, Any]]


class CodeReassemblyResponse(BaseModel):
    """Response model for reassembled code"""
    code: str
    source_file: str
    line_range: Dict[str, int]


class ExceptionResponseModel(BaseModel):
    """Model for exception endpoint responses"""
    status: str
    message: str
    security_issues_found: int
    details: Optional[Dict[str, Any]] = None


class SecurityIssue(BaseModel):
    """Model for security findings"""
    issue_type: str
    confidence: float
    description: str
    evidence: Dict[str, Any]
    recommendation: str
    related_cwe: Optional[str]

    class Config:
        json_encoders = {
            bytes: lambda v: v.decode('utf-8', errors='replace'),
        }


class ExceptionData(BaseModel):
    """Data model for incoming exception data"""
    scan_id: str
    exception_meta: dict
    request_headers: Optional[Dict]
    response_headers: Optional[Dict]
    form_data: Optional[Dict]
    form_fields: Optional[Dict]
    extracted_vars: Optional[Dict]

class DashboardException(BaseModel):
    """Standardized exception format for dashboard"""
    id: str
    scan_id: str = ""
    timestamp: str
    endpoint: str
    method: str
    exception_type: str
    severity: ExceptionSeverity
    description: str
    stack_trace: List[Dict]
    request_data: Optional[Dict]
    variables: Optional[Dict]
    raw_output: str
    security_issues: List[SecurityIssue] = []
    plugin: str

    class Config:
        json_encoders = {
            bytes: lambda v: v.decode('utf-8', errors='replace'),
        }

class EnvironmentData(BaseModel):
    """Model for environment data"""
    app_name: str
    environment: Dict[str, Any]

class EnvironmentResponseModel(BaseModel):
    """Response model for environment endpoint"""
    status: str
    message: str

class DashboardServer:
    def __init__(self):
        self.app = FastAPI(title="D4m8 Dashboard Server")
        self.active_connections: List[WebSocket] = []
        self.exceptions_store: List[DashboardException] = []
        self.environments_store: Dict[str, Dict] = {}
        self._load_persisted_state()
        self.setup_middleware()
        self.setup_routes()

    def _load_persisted_state(self) -> None:
        """Hydrate in-memory stores from ~/.vimana/monitor/ (best-effort)."""
        try:
            from core.api.backend.persist import load_environments, load_exceptions
        except Exception:
            return
        try:
            for row in load_exceptions():
                try:
                    self.exceptions_store.append(DashboardException(**row))
                except Exception:
                    continue
            self.environments_store = load_environments() or {}
        except Exception as exc:
            print(f"[monitor] persist load skipped: {exc}")

    def setup_middleware(self):
        """Configure middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):
        """Configure API routes"""

        @self.app.get("/", response_class=None)
        async def monitor_home():
            """Landing — /monitor is API; real UI is FuzzingDashboard (Next.js)."""
            from fastapi.responses import HTMLResponse
            return HTMLResponse(
                content="""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Vimana Exception Monitor</title>
<style>
  body{font-family:ui-sans-serif,system-ui,sans-serif;background:#0c1016;color:#e8eef6;
       margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center}
  .card{max-width:520px;padding:1.75rem 1.5rem;border:1px solid #2a3544;border-radius:10px;
        background:#151c26;line-height:1.5}
  h1{font-size:1.1rem;letter-spacing:.06em;text-transform:uppercase;margin:0 0 .5rem}
  p{color:#8b9bb0;font-size:.9rem;margin:.4rem 0}
  code{font-family:ui-monospace,monospace;font-size:.8rem;color:#3d9a7a}
  a{color:#6eb8ff;text-decoration:none} a:hover{text-decoration:underline}
  ul{margin:.6rem 0;padding-left:1.1rem;color:#c5d0dc;font-size:.85rem}
</style></head><body><div class="card">
<h1>Exception Monitor API</h1>
<p>This path is the <strong>JSON/WebSocket backend</strong>, not the React dashboard.</p>
<ul>
  <li><a href="exceptions">GET /exceptions</a></li>
  <li><a href="scans">GET /scans</a></li>
  <li><a href="demo/catalog">GET /demo/catalog</a></li>
  <li>POST /demo/seed — multi-app mock</li>
  <li>WS /ws — live feed</li>
</ul>
<p>Open the real UI:</p>
<p><code>cd core/api/frontend && npm run dev</code><br/>
→ <a href="http://127.0.0.1:3000" target="_blank" rel="noopener">http://127.0.0.1:3000</a></p>
<p>Query params: <code>?monitor=&lt;api-base&gt;</code> · <code>?scan=&lt;scan_id&gt;</code><br/>
Env: <code>NEXT_PUBLIC_MONITOR_URL</code> (default <code>http://127.0.0.1:8000</code>,
or this host + <code>/monitor</code> under Control).</p>
</div></body></html>""",
                status_code=200,
            )

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.handle_websocket_connection(websocket)

        @self.app.post("/exception", response_model=ExceptionResponseModel)
        async def receive_exception(data: ExceptionData):
            return await self.handle_new_exception(data)

        @self.app.get("/exceptions")
        async def get_exceptions(
            scan_id: Optional[str] = None,
            plugin: Optional[str] = None,
            limit: int = 200,
        ):
            items = list(self.exceptions_store)
            if scan_id:
                items = [e for e in items if (e.scan_id or '') == scan_id]
            if plugin:
                plug = plugin.strip().lower()
                items = [e for e in items if (e.plugin or '').lower() == plug]
            limit = max(1, min(int(limit or 200), 2000))
            sliced = items[-limit:]
            return {
                "exceptions": sliced,
                "count": len(sliced),
                "total_matching": len(items),
                "scan_id": scan_id,
                "plugin": plugin,
            }

        @self.app.get("/exceptions/{exception_id}")
        async def get_exception(exception_id: str):
            exception = next(
                (e for e in self.exceptions_store if e.id == exception_id),
                None
            )
            if not exception:
                raise HTTPException(status_code=404, detail="Exception not found")
            return exception

        @self.app.get("/scans")
        async def list_scans():
            """Aggregate exceptions by scan_id (newest activity last)."""
            buckets: Dict[str, Dict[str, Any]] = {}
            for exc in self.exceptions_store:
                sid = exc.scan_id or 'unknown'
                bucket = buckets.setdefault(sid, {
                    'scan_id': sid,
                    'count': 0,
                    'plugins': set(),
                    'severities': {},
                    'last_timestamp': None,
                })
                bucket['count'] += 1
                if exc.plugin:
                    bucket['plugins'].add(exc.plugin)
                sev = exc.severity.value if hasattr(exc.severity, 'value') else str(exc.severity)
                bucket['severities'][sev] = bucket['severities'].get(sev, 0) + 1
                ts = exc.timestamp
                if not bucket['last_timestamp'] or (ts and ts > bucket['last_timestamp']):
                    bucket['last_timestamp'] = ts
            scans = []
            for b in buckets.values():
                scans.append({
                    'scan_id': b['scan_id'],
                    'count': b['count'],
                    'plugins': sorted(b['plugins']),
                    'severities': b['severities'],
                    'last_timestamp': b['last_timestamp'],
                })
            scans.sort(key=lambda s: s.get('last_timestamp') or '', reverse=True)
            return {'scans': scans, 'count': len(scans)}

        @self.app.get("/scans/{scan_id}")
        async def get_scan(scan_id: str):
            items = [e for e in self.exceptions_store if (e.scan_id or '') == scan_id]
            if not items:
                raise HTTPException(status_code=404, detail="scan not found")
            return {
                'scan_id': scan_id,
                'count': len(items),
                'exceptions': items,
            }

        @self.app.post("/demo/seed")
        async def demo_seed(
            reset: bool = True,
            apps: Optional[str] = None,
        ):
            """
            Populate the monitor with multi-app mock exceptions + environments.
            Query: reset=true|false, apps=shop,blog (optional subset).
            """
            from core.api.backend.mock_seed import seed_into_server
            app_list = None
            if apps:
                app_list = [a.strip() for a in apps.split(',') if a.strip()]
            try:
                result = seed_into_server(self, reset=reset, apps=app_list)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f'seed failed: {exc}')
            # Notify WS clients with a fresh snapshot
            for connection in list(self.active_connections):
                try:
                    await connection.send_json({
                        'type': 'initial_data',
                        'data': [e.dict() for e in self.exceptions_store],
                    })
                except Exception:
                    pass
            return {'status': 'ok', **result}

        @self.app.post("/demo/reset")
        async def demo_reset():
            """Clear in-memory + persisted exceptions/environments."""
            self.exceptions_store.clear()
            self.environments_store.clear()
            try:
                from core.api.backend.persist import exceptions_path, environments_path
                for p in (exceptions_path(), environments_path()):
                    if p.exists():
                        p.unlink()
            except Exception as exc:
                raise HTTPException(status_code=500, detail=str(exc))
            return {'status': 'ok', 'cleared': True}

        @self.app.get("/demo/catalog")
        async def demo_catalog():
            from core.api.backend.mock_seed import MOCK_APPS, build_demo_payload
            preview = build_demo_payload()
            return {
                'apps': [
                    {
                        'name': a['name'],
                        'base_url': a['base_url'],
                        'plugin': a['plugin'],
                        'views': len(a['views']),
                    }
                    for a in MOCK_APPS
                ],
                'preview_summary': preview['summary'],
            }

        @self.app.post("/environment", response_model=EnvironmentResponseModel)
        async def receive_environment(data: Dict[str, Dict[str, Any]]):
            return await self.handle_new_environment(data)

        @self.app.get("/environments")
        async def get_environments():
            return {"environments": self.environments_store}

        @self.app.get("/environments/{app_name}")
        async def get_environment(app_name: str):
            if app_name not in self.environments_store:
                raise HTTPException(status_code=404, detail="Environment not found")
            return {"environment": self.environments_store[app_name]}

    async def handle_new_environment(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Process new environment data"""
        try:
            print(f"Received environment data: {data}")
            
            # Expect data in format {app_name: environment_dict}
            if not data or not isinstance(data, dict):
                print("Invalid data format received")
                raise ValueError("Invalid environment data format")
                
            for app_name, environment in data.items():
                print(f"Processing environment for {app_name}")
                # Store the environment data for this app
                self.environments_store[app_name] = environment
                print(f"Stored environment for {app_name}: {len(environment)} entries")
                
                # Broadcast environment update to connected clients
                await self.broadcast_environment_update(app_name, environment)

            try:
                from core.api.backend.persist import save_environments
                save_environments(self.environments_store)
            except Exception as persist_exc:
                print(f"[monitor] env persist skipped: {persist_exc}")
                
            return {"status": "success", "message": "Environment data processed"}
        except Exception as e:
            print(f"Exception in handle_new_environment: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error processing environment: {str(e)}")
        
    async def broadcast_environment_update(self, app_name: str, environment: Dict):
        """Broadcast environment update to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "type": "environment_update",
                    "data": {
                        "app_name": app_name,
                        "environment": environment
                    }
                })
            except Exception as e:
                print(f"Error broadcasting environment to client: {e}")
                
    async def handle_websocket_connection(self, websocket: WebSocket):
        """Handle new WebSocket connections"""
        await websocket.accept()
        self.active_connections.append(websocket)
        try:
            # Send existing exceptions
            if self.exceptions_store:
                await websocket.send_json({
                    "type": "initial_data",
                    "data": [exc.dict() for exc in self.exceptions_store]
                })
            
            # Keep connection alive
            while True:
                await websocket.receive_text()
                
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            self.active_connections.remove(websocket)

    def convert_security_findings(self, findings: List[SecurityFinding]) -> List[SecurityIssue]:
        """Convert SecurityFinding objects to SecurityIssue models"""
        converted_findings = []
        for finding in findings:
            # Sanitize evidence before creating SecurityIssue
            sanitized_evidence = self.sanitize_evidence(finding.evidence)
            converted_findings.append(
                SecurityIssue(
                    issue_type=finding.issue_type.value,
                    confidence=finding.confidence,
                    description=finding.description,
                    evidence=sanitized_evidence,
                    recommendation=finding.recommendation,
                    related_cwe=finding.related_cwe
                )
            )
        return converted_findings
    
    def sanitize_evidence(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize evidence data to ensure it can be JSON serialized"""
        def sanitize_value(value):
            if isinstance(value, (str, int, float, bool, type(None))):
                return value
            elif isinstance(value, (list, tuple)):
                return [sanitize_value(v) for v in value]
            elif isinstance(value, dict):
                return {str(k): sanitize_value(v) for k, v in value.items()}
            elif isinstance(value, bytes):
                return value.decode('utf-8', errors='replace')
            else:
                return str(value)

        return {str(k): sanitize_value(v) for k, v in evidence.items()}

    def determine_severity(self, exception_info: dict) -> ExceptionSeverity:
        """Enhanced severity determination including security findings"""
        # Get base severity
        base_severity = self._get_base_severity(exception_info)
        
        # Adjust severity based on security findings if available
        if security_issues := exception_info.get('security_issues', []):
            if any(issue.get('confidence', 0) > 0.8 for issue in security_issues):
                return ExceptionSeverity.CRITICAL
            elif any(issue.get('confidence', 0) > 0.6 for issue in security_issues):
                return ExceptionSeverity.HIGH
        
        return base_severity

    def _get_base_severity(self, exception_info: dict) -> ExceptionSeverity:
        """Determine base severity from exception type"""
        exception_type = exception_info.get('exception_type', '').lower()
        
        if any(critical in exception_type for critical in ['security', 'integrity', 'critical']):
            return ExceptionSeverity.CRITICAL
        elif any(high in exception_type for high in ['database', 'authentication']):
            return ExceptionSeverity.HIGH
        elif any(medium in exception_type for medium in ['validation', 'permission']):
            return ExceptionSeverity.MEDIUM
        return ExceptionSeverity.LOW

    def format_exception(self, data: ExceptionData) -> DashboardException:
        """Format incoming exception data for dashboard"""
        meta = data.exception_meta
        summary = meta.get('summary', {})
        
        # Prepare data for security analysis
        analysis_data = {
            "exception_type": summary.get('Exception Type', ''),
            "description": summary.get('Exception Value', ''),
            "stack_trace": meta.get('traceback', []),
            "endpoint": summary.get('Request URL', ''),
            "method": summary.get('Request Method', '')
        }
        
        # Perform security analysis exception → security issue
        analyzer = DjangoExceptionAnalyzer()
        security_findings = analyzer.analyze_exception(analysis_data)
        security_issues = self.convert_security_findings(security_findings)
        '''
        for finding in security_findings:
            print(f"Issue Type: {finding.issue_type.value}")
            print(f"Confidence: {finding.confidence * 100}%")
            print(f"Description: {finding.description}")
            print(f"Evidence: {finding.evidence}")
            print(f"Recommendation: {finding.recommendation}")
            print(f"Related CWE: {finding.related_cwe}")
            print("="*100)
        '''
        
        # Update exception_info with security findings for severity determination
        meta['security_issues'] = [issue.dict() for issue in security_issues]

        return DashboardException(
            id=meta.get('exception_id', ''),
            scan_id=data.scan_id or meta.get('scan_id', '') or '',
            timestamp=datetime.now().isoformat(),
            endpoint=summary.get('Request URL', ''),
            method=summary.get('Request Method', ''),
            exception_type=summary.get('Exception Type', ''),
            severity=self.determine_severity(meta),
            description=summary.get('Exception Value', ''),
            stack_trace=meta.get('traceback', []),
            request_data={
                'headers': data.request_headers,
                'form_data': data.form_data,
                'form_fields': data.form_fields
            },
            variables=data.extracted_vars,
            raw_output=json.dumps(meta, indent=2),
            security_issues=security_issues,
            plugin=meta.get('plugin', '')
        )

    def extract_code_snippets(self, exceptions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and organize code snippets from exceptions"""
        snippets = []
        for exception in exceptions:
            try:
                # Parse raw output to get view_trigger
                raw_output = json.loads(exception.get('raw_output', '{}'))
                view_trigger = raw_output.get('view_trigger', {})
                
                if not view_trigger:
                    continue

                # Extract stack trace for the view file
                stack_trace = exception.get('stack_trace', [])
                view_file_trace = next(
                    (trace for trace in stack_trace 
                     if trace.get('file') == view_trigger.get('fullpath')),
                    None
                )

                if view_file_trace and 'code_snippet' in view_file_trace:
                    snippets.append({
                        'file': view_trigger['fullpath'],
                        'line_number': int(view_trigger.get('line_number', 0)),
                        'code': view_file_trace['code_snippet']
                    })

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Error processing exception for code reassembly: {e}")
                continue

        return snippets

    def reassemble_code(self, snippets: List[Dict[str, Any]]) -> CodeReassemblyResponse:
        """Reassemble code from collected snippets"""
        if not snippets:
            return CodeReassemblyResponse(
                code="No code snippets found in the selected exceptions.",
                source_file="",
                line_range={"start": 0, "end": 0}
            )

        # Group snippets by file
        file_snippets = {}
        for snippet in snippets:
            file_path = snippet['file']
            if file_path not in file_snippets:
                file_snippets[file_path] = []
            file_snippets[file_path].append(snippet)

        # Process the file with the most snippets
        target_file = max(file_snippets.keys(), key=lambda k: len(file_snippets[k]))
        target_snippets = file_snippets[target_file]

        # Sort snippets by line number and merge
        sorted_snippets = sorted(target_snippets, key=lambda x: x['line_number'])
        
        # Create a map of line numbers to code lines
        code_map = {}
        for snippet in sorted_snippets:
            base_line = snippet['line_number']
            for i, line in enumerate(snippet['code']):
                code_map[base_line + i] = line

        # Determine the line range
        min_line = min(code_map.keys())
        max_line = max(code_map.keys())

        # Build the reassembled code
        reassembled_lines = []
        current_line = min_line
        while current_line <= max_line:
            if current_line in code_map:
                reassembled_lines.append(code_map[current_line])
            else:
                reassembled_lines.append('    # ... missing code ...')
            current_line += 1

        return CodeReassemblyResponse(
            code='\n'.join(reassembled_lines),
            source_file=target_file,
            line_range={"start": min_line, "end": max_line}
        )

    async def broadcast_exception(self, exception: DashboardException):
        """Broadcast exception to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "type": "new_exception",
                    "data": exception.dict()
                })
            except Exception as e:
                print(f"Error broadcasting to client: {e}")

    async def handle_new_exception(self, data: ExceptionData) -> ExceptionResponseModel:
        """Process and broadcast new exception"""
        try:
            exception = self.format_exception(data)

            self.exceptions_store.append(exception)
            try:
                from core.api.backend.persist import append_exception
                append_exception(exception.dict())
            except Exception as persist_exc:
                print(f"[monitor] exception persist skipped: {persist_exc}")
            await self.broadcast_exception(exception)
            return ExceptionResponseModel(
                status="success",
                message="Exception processed and broadcast",
                security_issues_found=len(exception.security_issues),
                details={
                    "exception_id": exception.id,
                    "scan_id": exception.scan_id,
                    "severity": exception.severity.value
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing exception: {str(e)}")

    async def handle_code_reassembly(self, request: CodeReassemblyRequest) -> CodeReassemblyResponse:
        """Handle code reassembly request"""
        try:
            snippets = self.extract_code_snippets(request.exceptions)
            return self.reassemble_code(snippets)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error reassembling code: {str(e)}"
            )

    @staticmethod
    def find_free_port(start_port: int = 8000, max_port: int = 8020) -> int:
        """Find an available port"""
        for port in range(start_port, max_port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        raise OSError(f"Could not find a free port between {start_port} and {max_port}")

    def run(self, host: str = "127.0.0.1", port: int = None):
        """Run the dashboard server"""
        try:
            if port is None:
                port = self.find_free_port()
            
            print(f"Starting D4m8 dashboard server on http://{host}:{port}")
            uvicorn.run(self.app, host=host, port=port, reload=False)
        except Exception as e:
            print(f"Error starting server: {e}")
            alternative_port = self.find_free_port(port + 1 if port else 8001)
            print(f"Trying alternative port: {alternative_port}")
            uvicorn.run(self.app, host=host, port=alternative_port, reload=False)


def main():
    """Entry point for the dashboard server"""
    parser = argparse.ArgumentParser(description='D4m8 Dashboard Server')
    parser.add_argument('--port', type=int, help='Port to run the server on')
    parser.add_argument('--host', type=str, default="127.0.0.1", 
                       help='Host to run the server on')
    
    args = parser.parse_args()
    server = DashboardServer()
    server.run(host=args.host, port=args.port)


# Create server instance and expose app for uvicorn
server = DashboardServer()
app = server.app

if __name__ == "__main__":
    main()