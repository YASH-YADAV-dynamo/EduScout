import os
from contextlib import asynccontextmanager
from pathlib import Path

import fastmcp.settings as mcp_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp.utilities.lifespan import combine_lifespans

from app.config import settings
from app.database.db import init_db
from app.mcp_server import mcp
from app.routes import auth, onboarding, telegram, whatsapp, webhooks
from app.routes.sse import get_sse_app
from app.services.scheduler import start_scheduler, stop_scheduler

# ChatGPT Apps SDK expects GET /sse and POST /messages
mcp_settings.message_path = "/messages"
mcp_settings.stateless_http = True

mcp_sse_app = get_sse_app()
mcp_streamable_app = mcp.http_app(transport="streamable-http", stateless_http=True, path="/mcp")

OAUTH_EXACT_PATHS = {"/authorize", "/token", "/register", "/revoke", "/consent", "/userinfo"}
FASTMCP_AUTH_PATHS = {"/auth/callback"}


def _route_to_streamable(path: str) -> bool:
    return path.startswith("/mcp") or path.startswith("/.well-known/oauth-protected-resource/mcp")


def _route_to_sse(path: str) -> bool:
    if path == "/sse" or path.startswith("/messages"):
        return True
    if path.startswith("/.well-known/"):
        return True
    if path in OAUTH_EXACT_PATHS or path in FASTMCP_AUTH_PATHS:
        return True
    return False


@asynccontextmanager
async def app_lifespan(_app: FastAPI):
    init_db()
    start_scheduler()
    base = settings.effective_base_url
    if mcp.auth:
        print(f"[oauth] enabled — base_url={base}")
        print(f"[oauth] ChatGPT/Claude connector URL (SSE):        {base}/sse")
        print(f"[oauth] Claude connector URL (Streamable HTTP):    {base}/mcp")
        print(f"[oauth] Google redirect URI:                       {base}/auth/callback")
        print(f"[oauth] Token lifetimes — access: 1 day, refresh: 7 days")
        if not base.startswith("https://"):
            print("[oauth] WARNING: base_url must be https (use ngrok PUBLIC_BASE_URL, not localhost)")
    else:
        print("[oauth] disabled — guest mode (MCP_OAUTH_ENABLED=false or missing Google creds)")
        print(f"[mcp] SSE connector URL:              {base}/sse")
        print(f"[mcp] Streamable HTTP connector URL:  {base}/mcp")
    print(f"[webhooks] Supabase webhook endpoint: {base}/webhooks/supabase")
    yield
    stop_scheduler()


app = FastAPI(
    title="Study Abroad Agent",
    lifespan=combine_lifespans(app_lifespan, mcp_sse_app.lifespan, mcp_streamable_app.lifespan),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(whatsapp.router)
app.include_router(telegram.router)
app.include_router(webhooks.router)


@app.get("/health")
def health():
    base = settings.effective_base_url
    google_redirect = f"{base}/auth/callback"
    return {
        "status": "ok",
        "service": "study-abroad-agent",
        "oauth_enabled": settings.oauth_active and bool(mcp.auth),
        "mcp_oauth_enabled": settings.mcp_oauth_enabled,
        "base_url": base,
        "google_configured": bool(settings.google_client_id and settings.google_client_secret),
        "env_file_exists": (Path(__file__).resolve().parent.parent / ".env").exists(),
        "chatgpt_connector_url": f"{base}/sse",
        "google_redirect_uri": google_redirect,
        "google_javascript_origin": base,
        "chatgpt_auth_mode": "OAuth: Yes" if settings.oauth_active else "OAuth: No",
        "supabase_webhook_url": f"{base}/webhooks/supabase",
        "oauth_setup_checklist": [
            f"Add Authorized redirect URI in Google Cloud Console: {google_redirect}",
            f"Add Authorized JavaScript origin: {base}",
            "Restart uvicorn after any .env change (reload does not pick up .env)",
            "Run ngrok on the same port as uvicorn: ngrok http 8000",
            "Update PUBLIC_BASE_URL in .env whenever ngrok URL changes",
            "If OAuth popup hangs, click through ngrok 'Visit Site' warning in the popup",
        ],
    }


class NgrokSkipWarningMiddleware:
    """Help API clients (ChatGPT) skip ngrok free-tier interstitial on API calls."""

    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.inner_app(scope, receive, send)
            return

        async def send_with_header(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"ngrok-skip-browser-warning", b"1"))
                message = {**message, "headers": headers}
            await send(message)

        await self.inner_app(scope, receive, send_with_header)


class MCPDispatchMiddleware:
    """Route MCP + OAuth traffic to the correct FastMCP Starlette apps."""

    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")

            # ChatGPT may request root protected-resource metadata (RFC 9728).
            if path == "/.well-known/oauth-protected-resource":
                scope = {**scope, "path": "/.well-known/oauth-protected-resource/sse"}

            path = scope.get("path", "")
            if _route_to_streamable(path):
                await mcp_streamable_app(scope, receive, send)
                return
            if _route_to_sse(path):
                await mcp_sse_app(scope, receive, send)
                return
        await self.inner_app(scope, receive, send)


app = MCPDispatchMiddleware(NgrokSkipWarningMiddleware(app))


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
