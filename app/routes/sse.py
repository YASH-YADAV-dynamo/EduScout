"""MCP SSE and message endpoints are served by the FastMCP Starlette app.

See app/main.py — GET /sse and POST /messages are wired via mcp.http_app(transport='sse').
"""

from fastmcp import FastMCP

from app.mcp_server import mcp


def get_sse_app():
    return mcp.http_app(transport="sse", stateless_http=True)
