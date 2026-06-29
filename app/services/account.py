from app.services.session import is_google_signed_in
from app.services.link import get_channels_for_user
from app.services.profile import get_profile
from app.services.study_plan import get_plan, list_plans
from app.services.user import ensure_public_id, get_user


def get_account_summary(user_id: int, plan_id: int | None = None) -> dict:
    user = get_user(user_id)
    if not user:
        return {"error": f"User {user_id} not found"}

    public_id = user.get("public_id") or ensure_public_id(user_id)
    plans = list_plans(user_id)
    active_plan = get_plan(plan_id) if plan_id else (plans[0] if plans else None)
    profile = get_profile(active_plan["id"]) if active_plan else None
    channels = get_channels_for_user(user_id)

    return {
        "user_id": user_id,
        "public_id": public_id,
        "esid": user.get("esid"),
        "overall_score": user.get("overall_score", 0),
        "name": user["name"],
        "email": user["email"],
        "signed_in_with_google": bool(user.get("google_sub")) or is_google_signed_in(),
        "mcp_oauth_at_connect": is_google_signed_in(),
        "plan_id": active_plan["id"] if active_plan else None,
        "plan_title": active_plan["title"] if active_plan else None,
        "profile": profile or {},
        "linked_channels": channels,
        "plans_count": len(plans),
    }
