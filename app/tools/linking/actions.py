from fastmcp import FastMCP
from fastmcp.apps.config import AppConfig, ResourceCSP

from app.services.college_subscriptions import (
    add_subscription,
    count_subscriptions,
    list_subscriptions,
    remove_subscription,
)
from app.services.link import generate_link_code
from app.services.profile import get_profile
from app.services.study_plan import get_plan
from app.services.task import list_tasks
from app.services.university import list_universities
from app.tools.constants import WIDGET_URIS


def register(mcp: FastMCP) -> None:
    @mcp.tool
    def create_link_code(user_id: int) -> dict:
        """Generate 24h linking code for WhatsApp/Telegram. Aliases: link_code, get_code."""
        return generate_link_code(user_id)

    @mcp.tool(
        app=AppConfig(resource_uri=WIDGET_URIS["dashboard"], csp=ResourceCSP(connect_domains=["*"])),
    )
    def show_dashboard(plan_id: int, user_id: int | None = None) -> dict:
        """Full dashboard widget. Aliases: dashboard, home, overview."""
        plan = get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        uid = user_id or plan["user_id"]
        profile = get_profile(plan_id) or {}
        tasks = list_tasks(plan_id)
        universities = list_universities(plan_id)
        link = generate_link_code(uid)
        pending = sum(1 for t in tasks if t.get("status") == "pending")

        return {
            "plan_id": plan_id,
            "user_id": uid,
            "plan_title": plan["title"],
            "plan_status": plan["status"],
            "profile": profile,
            "tasks": tasks,
            "universities": universities,
            "link_code": link["code"],
            "stats": {
                "tasks_total": len(tasks),
                "tasks_pending": pending,
                "universities_total": len(universities),
            },
        }

    @mcp.tool
    def subscribe_college_notification(plan_id: int, university_id: int) -> dict:
        """Subscribe user to college deadline notifications (max 10). Returns Telegram deep link."""
        plan = get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        return add_subscription(plan["user_id"], university_id)

    @mcp.tool
    def get_college_subscriptions(plan_id: int) -> dict:
        """List user's college notification subscriptions with count."""
        plan = get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        subs = list_subscriptions(plan["user_id"])
        return {
            "subscriptions": subs,
            "count": len(subs),
            "max": 10,
        }

    @mcp.tool
    def unsubscribe_college(plan_id: int, university_id: int) -> dict:
        """Remove a college notification subscription."""
        plan = get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        removed = remove_subscription(plan["user_id"], university_id)
        return {
            "removed": removed,
            "university_id": university_id,
            "count": count_subscriptions(plan["user_id"]),
            "max": 10,
        }
