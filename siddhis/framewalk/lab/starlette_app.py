from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.exceptions import HTTPException
import uvicorn

async def homepage(request):
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head><title>Starlette Test App</title></head>
        <body>
            <h1>Hello from Starlette!</h1>
            <p>This is a minimal Starlette application for testing Framewalk.</p>
            <ul>
                <li><a href='/api/status'>API Status</a></li>
                <li><a href='/about'>About</a></li>
            </ul>
        </body>
        </html>
        """
    )

async def about(request):
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head><title>About - Starlette</title></head>
        <body>
            <h1>About Starlette</h1>
            <p>Starlette Framework Detection Test</p>
            <p>Starlette is a lightweight ASGI framework/toolkit.</p>
        </body>
        </html>
        """
    )

async def api_status(request):
    return JSONResponse({
        "status": "running",
        "framework": "starlette",
        "version": "0.36.3"
    })

async def trigger_error(request):
    raise HTTPException(status_code=500, detail="Test error for Starlette framework detection")

routes = [
    Route("/", homepage),
    Route("/about", about),
    Route("/api/status", api_status),
    Route("/error", trigger_error),
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 