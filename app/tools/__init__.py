from fastmcp import FastMCP

from app.tools.account import register as register_account
from app.tools.documents import register as register_documents
from app.tools.linking import register as register_linking
from app.tools.planning import register as register_planning
from app.tools.uni_research import register as register_uni_research
from app.tools.user_input import register as register_user_input


def register_all_tools(mcp: FastMCP) -> None:
    register_account(mcp)
    register_user_input(mcp)
    register_uni_research(mcp)
    register_documents(mcp)
    register_planning(mcp)
    register_linking(mcp)
