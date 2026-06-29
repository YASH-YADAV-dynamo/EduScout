from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/success")
def auth_success():
    """Shown after manual OAuth flows; ChatGPT/Claude MCP uses its own callback redirect."""
    html = """
<!DOCTYPE html>
<html>
<head>
  <title>Connected!</title>
  <meta charset="utf-8" />
  <style>
    body { font-family: sans-serif; text-align: center; padding: 60px 20px; background: #f0fdf4; color: #166534; }
    .card { background: white; border-radius: 12px; padding: 40px; max-width: 400px; margin: 0 auto; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
    h2 { margin: 0 0 12px; font-size: 1.5rem; }
    p  { margin: 0; color: #555; font-size: 0.95rem; }
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size:2.5rem">✅</div>
    <h2>Connected!</h2>
    <p>Google sign-in successful. You can close this tab.</p>
  </div>
  <script>
    // Auto-close after 2 s (works when opened as a popup by the MCP client)
    setTimeout(function () { window.close(); }, 2000);
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/error")
def auth_error():
    base = settings.effective_base_url
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <title>Connection Failed</title>
  <meta charset="utf-8" />
  <style>
    body {{ font-family: sans-serif; text-align: center; padding: 60px 20px; background: #fef2f2; color: #991b1b; }}
    .card {{ background: white; border-radius: 12px; padding: 40px; max-width: 480px; margin: 0 auto; box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
    h2  {{ margin: 0 0 12px; font-size: 1.4rem; }}
    ul  {{ text-align: left; font-size: 0.85rem; color: #555; line-height: 1.7; }}
    code {{ background: #f3f4f6; padding: 2px 5px; border-radius: 4px; font-size: 0.8rem; }}
    .retry {{ display:inline-block; margin-top:20px; padding:10px 24px; background:#1d4ed8; color:white; border-radius:8px; text-decoration:none; font-size:.9rem; }}
  </style>
</head>
<body>
  <div class="card">
    <div style="font-size:2.5rem">❌</div>
    <h2>Google Sign-In Failed</h2>
    <p style="color:#555;font-size:.9rem;margin-bottom:16px">Check these common causes:</p>
    <ul>
      <li>Authorized redirect URI in Google Cloud Console must be exactly:<br/>
          <code>{base}/auth/callback</code></li>
      <li>Authorized JavaScript origin must be:<br/>
          <code>{base}</code></li>
      <li><code>PUBLIC_BASE_URL</code> in <code>.env</code> must match your ngrok URL</li>
      <li>Restart uvicorn after any <code>.env</code> change</li>
    </ul>
    <a class="retry" href="{base}/authorize">Try Again</a>
  </div>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/setup")
def auth_setup():
    """OAuth setup checklist for ChatGPT + Claude + Google."""
    base = settings.effective_base_url
    return {
        "google_redirect_uri": f"{base}/auth/callback",
        "google_javascript_origin": base,
        "mcp_connector_url_sse": f"{base}/sse",
        "mcp_connector_url_streamable": f"{base}/mcp",
        "token_lifetime": {
            "access_token_seconds": 86400,
            "access_token_human": "1 day",
            "refresh_token_seconds": 604800,
            "refresh_token_human": "7 days",
        },
        "note": "FastMCP handles /auth/callback — do NOT use /auth/success as Google redirect URI.",
        "steps": [
            "Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client (Web application)",
            f"Authorized redirect URIs → add exactly: {base}/auth/callback",
            f"Authorized JavaScript origins → add exactly: {base}",
            f".env: PUBLIC_BASE_URL={base}",
            "Restart uvicorn after .env changes (reload does NOT re-read .env)",
            "ngrok http 8000  (same port as uvicorn)",
            f"ChatGPT/Claude connector URL: {base}/sse",
            "When connecting: enable OAuth → Yes, then click Connect → sign in with Google",
        ],
    }
