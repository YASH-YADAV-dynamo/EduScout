"""MCP message endpoint is bundled with the SSE transport app.

See app/routes/sse.py and app/main.py.
"""

from app.routes.sse import get_sse_app

__all__ = ["get_sse_app"]
