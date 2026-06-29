from pathlib import Path

from fastmcp import FastMCP
from fastmcp.resources import FileResource
from fastmcp.utilities.mime import UI_MIME_TYPE

from app.config import WIDGETS_DIR, settings
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.tools import register_all_tools
from app.tools.constants import WIDGET_URIS


def _build_auth():
    if not settings.oauth_active:
        return None

    from fastmcp.server.auth.providers.google import GoogleProvider

    # Session token (access): 1 day  = 86_400 seconds
    # Refresh token:          7 days = 604_800 seconds
    return GoogleProvider(
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        base_url=settings.effective_base_url,
        required_scopes=["openid", "email", "profile"],
        # "external" = Google's own consent screen handles consent; no built-in page shown.
        require_authorization_consent="external",
        # FastMCP-issued access token lives for 1 day regardless of Google's shorter TTL.
        fastmcp_access_token_expiry_seconds=86_400,
        # FastMCP-issued refresh token lives for 7 days.
        fallback_refresh_token_expiry_seconds=604_800,
        # Force offline access + consent so Google always issues a refresh token.
        extra_authorize_params={
            "access_type": "offline",
            "prompt": "consent",
        },
    )


mcp = FastMCP(
    name="Study Abroad Agent",
    instructions=SYSTEM_PROMPT,
    auth=_build_auth(),
)


def _load_widget_html(name: str) -> str:
    folder = WIDGETS_DIR / name
    theme = (WIDGETS_DIR / "theme.css").read_text(encoding="utf-8")
    stage_layout = ""
    if name.startswith("profile_form_stage"):
        stage_layout = (WIDGETS_DIR / "stage_layout.css").read_text(encoding="utf-8")
    html = (folder / "index.html").read_text(encoding="utf-8")
    css = (folder / "style.css").read_text(encoding="utf-8")
    js = (folder / "app.js").read_text(encoding="utf-8")
    if name.startswith("profile_form_stage"):
        shared = (WIDGETS_DIR / "stage_shared.js").read_text(encoding="utf-8")
        js = shared + "\n" + js
    combined_css = f"{theme}\n{stage_layout}\n{css}"
    html = html.replace('<link rel="stylesheet" href="style.css" />', f"<style>{combined_css}</style>")
    html = html.replace('<script src="app.js"></script>', f"<script>{js}</script>")
    return html


def _register_widgets() -> None:
    for name, uri in WIDGET_URIS.items():
        html_path = WIDGETS_DIR / name / "bundle.html"
        html_path.write_text(_load_widget_html(name), encoding="utf-8")
        mcp.add_resource(
            FileResource(
                uri=uri,
                path=html_path,
                mime_type=UI_MIME_TYPE,
            )
        )


_register_widgets()
register_all_tools(mcp)


@mcp.prompt
def system_prompt() -> str:
    """System instructions for the study abroad agent."""
    return SYSTEM_PROMPT
