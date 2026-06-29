"""Resolve the current user from MCP OAuth (Google sign-in at connect time)."""

from app.services.user import get_or_create_by_google


def resolve_current_user() -> dict:
    """Return DB user from Google OAuth token, or a guest if OAuth is off / not connected."""
    token = _get_token()
    if token and token.claims:
        sub = token.claims.get("sub")
        email = token.claims.get("email")
        name = token.claims.get("name") or (email.split("@")[0] if email else "Student")
        if sub and email:
            return get_or_create_by_google(google_sub=sub, email=email, name=name)

    from app.services.onboarding import _guest_user

    return _guest_user()


def is_google_signed_in() -> bool:
    token = _get_token()
    return bool(token and token.claims and token.claims.get("sub"))


def _get_token():
    """
    Safely retrieve the FastMCP access token for the current request.

    FastMCP stores the verified token in a context-var that is only populated
    during an active MCP request.  Calling this outside a request (e.g. during
    startup, scheduler jobs, or Telegram/WhatsApp webhooks) raises a LookupError
    or ValueError — we catch all exceptions so non-MCP code paths always get a
    clean None instead of a traceback.
    """
    try:
        from fastmcp.server.dependencies import get_access_token

        return get_access_token()
    except Exception:
        return None
