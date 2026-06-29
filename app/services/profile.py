from app.services.profile_extended import get_full_profile, patch_profile


def save_profile(
    plan_id: int,
    *,
    degree: str | None = None,
    major: str | None = None,
    cgpa: float | None = None,
    budget: float | None = None,
    budget_range: str | None = None,
    target_intake: str | None = None,
    priority: str | None = None,
    region: str | None = None,
    resume_url: str | None = None,
    **extra,
) -> dict:
    fields = {
        k: v
        for k, v in {
            "degree": degree,
            "major": major,
            "cgpa": cgpa,
            "budget": budget,
            "budget_range": budget_range,
            "target_intake": target_intake,
            "priority": priority,
            "region": region,
            "resume_url": resume_url,
            **extra,
        }.items()
        if v is not None
    }
    return patch_profile(plan_id, **fields)


def get_profile(plan_id: int) -> dict | None:
    return get_full_profile(plan_id)


def profile_summary(plan_id: int) -> str:
    p = get_full_profile(plan_id) or {}
    parts = []
    for label, key in [
        ("Degree", "degree"),
        ("Major", "major"),
        ("CGPA", "cgpa"),
        ("Target degree", "target_degree"),
        ("Target field", "target_field"),
        ("Budget", "budget_range"),
        ("Intake", "target_intake"),
        ("Priority", "priority"),
        ("Region", "region"),
    ]:
        val = p.get(key)
        if val:
            parts.append(f"{label}: {val}")
    return "; ".join(parts) if parts else "No profile saved yet."
