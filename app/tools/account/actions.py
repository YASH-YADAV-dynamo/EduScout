from fastmcp import FastMCP
from fastmcp.apps.config import AppConfig, ResourceCSP

from app.services.account import get_account_summary
from app.services.profile import save_profile
from app.services.session import resolve_current_user
from app.services.user import get_or_create_user, get_user
from app.tools.constants import WIDGET_URIS


def register(mcp: FastMCP) -> None:
    @mcp.tool
    def get_my_profile(user_id: int | None = None, plan_id: int | None = None) -> dict:
        """Get account info, unique public ID, linked channels, and study profile. Aliases: profile, my_info, whoami."""
        if user_id is None:
            user_id = resolve_current_user()["id"]
        return get_account_summary(user_id, plan_id)

    @mcp.tool(
        app=AppConfig(resource_uri=WIDGET_URIS["account"], csp=ResourceCSP(connect_domains=["*"])),
    )
    def show_account(user_id: int | None = None, plan_id: int | None = None) -> dict:
        """Show account widget with SAA- ID, Google status, linked channels, profile. Aliases: account, my_id."""
        if user_id is None:
            user_id = resolve_current_user()["id"]
        return get_account_summary(user_id, plan_id)

    @mcp.tool
    def ensure_user(email: str, name: str) -> dict:
        """Bootstrap guest or OAuth user. Alias: init."""
        return get_or_create_user(email, name)

    @mcp.tool
    def get_esid(user_id: int | None = None) -> dict:
        """Return user's ESID for Telegram linking and account display."""
        if user_id is None:
            user_id = resolve_current_user()["id"]
        user = get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return {
            "user_id": user_id,
            "esid": user.get("esid"),
            "email": user.get("email"),
            "name": user.get("name"),
        }

    @mcp.tool
    def update_profile(
        plan_id: int,
        degree: str | None = None,
        major: str | None = None,
        cgpa: float | None = None,
        budget: float | None = None,
        budget_range: str | None = None,
        target_intake: str | None = None,
        priority: str | None = None,
        region: str | None = None,
        resume_url: str | None = None,
        target_degree: str | None = None,
        target_field: str | None = None,
    ) -> dict:
        """Patch any profile field. Aliases: edit_profile, update_info."""
        return save_profile(
            plan_id,
            degree=degree,
            major=major,
            cgpa=cgpa,
            budget=budget,
            budget_range=budget_range,
            target_intake=target_intake,
            priority=priority,
            region=region,
            resume_url=resume_url,
            target_degree=target_degree,
            target_field=target_field,
        )
