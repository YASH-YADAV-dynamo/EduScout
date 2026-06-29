import secrets

from app.services.onboarding_stages import record_stage_snapshot
from app.services.profile import get_profile
from app.services.profile_extended import patch_profile
from app.services.profile_validation import check_profile_ready
from app.services.study_plan import create_plan, get_plan, update_plan_status
from app.services.user import get_or_create_user, get_user


def _guest_user() -> dict:
    token = secrets.token_hex(4)
    return get_or_create_user(f"guest-{token}@studyabroad.local", "Student")


def profile_summary(profile: dict) -> str:
    priority_labels = {
        "cheapest": "Cheapest option",
        "best_universities": "Best universities",
        "salary": "Highest salary after graduation",
        "immigration": "Easiest immigration pathway",
    }
    lines = [
        f"- Region: {profile.get('region') or '—'}",
        f"- Degree: {profile.get('degree') or '—'}",
        f"- Field: {profile.get('major') or profile.get('target_field') or '—'}",
        f"- Target degree: {profile.get('target_degree') or '—'}",
        f"- CGPA / %: {profile.get('cgpa') or '—'}",
        f"- University: {profile.get('university_name') or '—'}",
        f"- Budget: {profile.get('budget_range') or profile.get('budget_usd') or '—'}",
        f"- Target intake: {profile.get('target_intake') or '—'}",
        f"- Priority: {priority_labels.get(profile.get('priority'), profile.get('priority') or '—')}",
    ]
    countries = profile.get("preferred_countries")
    if countries:
        lines.append(f"- Countries: {', '.join(countries) if isinstance(countries, list) else countries}")
    exams = profile.get("exams") or {}
    ielts = exams.get("ielts_overall") or exams.get("ielts_expected")
    if ielts:
        lines.append(f"- IELTS: {ielts}")
    return "\n".join(lines)


def build_roadmap_prompt(plan_id: int, profile: dict) -> str:
    summary = profile_summary(profile)
    ready = check_profile_ready(plan_id)
    if ready["ready"]:
        return (
            f"Profile complete for plan #{plan_id}.\n\n{summary}\n\n"
            "Next steps:\n"
            "1. Call generate_candidate_score\n"
            "2. Call search_universities\n"
            "3. Research tiered shortlist and add_university_to_plan for each\n"
            "4. Call show_university_basket\n"
            "5. Offer generate_resume_draft and generate_sop_outline"
        )
    missing = ", ".join(m["field"] for m in ready["missing_fields"])
    return (
        f"Profile saved for plan #{plan_id} ({ready['profile_completeness']}% complete).\n\n"
        f"{summary}\n\n"
        f"Missing for search: {missing}. Use collect_* tools to fill gaps, then check_profile_ready."
    )


def start_onboarding(
    *,
    plan_id: int | None = None,
    user_id: int | None = None,
    email: str | None = None,
    name: str | None = None,
    region: str = "Europe",
) -> dict:
    if user_id is None:
        if email and name:
            user = get_or_create_user(email, name)
            user_id = user["id"]
        else:
            user = _guest_user()
            user_id = user["id"]

    if plan_id is None:
        plan = create_plan(user_id, f"Study Abroad — {region}")
        plan_id = plan["id"]
        patch_profile(plan_id, region=region)

    profile = get_profile(plan_id) or {"plan_id": plan_id, "region": region}
    user_row = get_user(user_id)
    return {
        "plan_id": plan_id,
        "user_id": user_id,
        "public_id": user_row.get("public_id") if user_row else None,
        "esid": user_row.get("esid") if user_row else None,
        "region": profile.get("region") or region,
        "step": 0,
        "profile": {**profile, "plan_id": plan_id},
    }


def save_onboarding(
    plan_id: int,
    *,
    complete: bool = False,
    degree: str | None = None,
    major: str | None = None,
    cgpa: float | None = None,
    budget_range: str | None = None,
    target_intake: str | None = None,
    priority: str | None = None,
    region: str | None = None,
    target_degree: str | None = None,
    target_field: str | None = None,
    university_name: str | None = None,
    institution_tier: str | None = None,
    budget_usd: float | None = None,
    preferred_countries: list | None = None,
    ielts_expected: float | None = None,
    gre_taken: bool | None = None,
    has_papers: bool | None = None,
    full_time_months: int | None = None,
    scholarship_seeking: bool | None = None,
    campus_type: str | None = None,
    post_study_goal: str | None = None,
    **extra,
) -> dict:
    if not get_plan(plan_id):
        return {"error": f"Plan {plan_id} not found", "plan_id": plan_id}

    existing = get_profile(plan_id) or {}

    core: dict = {
        k: v
        for k, v in {
            "degree": degree,
            "major": major,
            "cgpa": cgpa,
            "budget_range": budget_range,
            "target_intake": target_intake,
            "priority": priority,
            "region": region,
            "target_degree": target_degree,
            "target_field": target_field,
            "university_name": university_name,
            "institution_tier": institution_tier,
            "budget_usd": budget_usd,
            "scholarship_seeking": scholarship_seeking,
            "campus_type": campus_type,
            "post_study_goal": post_study_goal,
            **extra,
        }.items()
        if v is not None
    }

    if preferred_countries is not None:
        core["preferred_countries_json"] = preferred_countries

    exams = dict(existing.get("exams") or {})
    exams_updated = False
    if ielts_expected is not None:
        exams["ielts_expected"] = ielts_expected
        exams_updated = True
    if gre_taken is not None:
        exams["gre_taken"] = gre_taken
        exams_updated = True
    if exams_updated:
        core["exams_json"] = exams

    research = dict(existing.get("research") or {})
    if has_papers is not None:
        research["has_papers"] = has_papers
        core["research_json"] = research

    if full_time_months is not None:
        work = dict(existing.get("work") or {})
        jobs = list(work.get("jobs") or [])
        if jobs:
            jobs[0] = {**jobs[0], "months": full_time_months}
        else:
            jobs = [{"months": full_time_months}]
        work["jobs"] = jobs
        core["work_json"] = work

    stage = 3 if complete else 1
    core["form_stage_complete"] = stage
    profile = patch_profile(plan_id, **core)

    stage_snapshot = {
        k: v
        for k, v in {
            "degree": degree,
            "major": major,
            "cgpa": cgpa,
            "region": region,
            "target_degree": target_degree,
            "target_field": target_field,
            "ielts_expected": ielts_expected,
            "gre_taken": gre_taken,
            "has_papers": has_papers,
            "full_time_months": full_time_months,
        }.items()
        if v is not None
    }
    if complete:
        for s in (1, 2, 3):
            record_stage_snapshot(plan_id, s, stage_snapshot)
    else:
        record_stage_snapshot(plan_id, 1, stage_snapshot)

    result = {
        "plan_id": plan_id,
        "profile": profile,
        "complete": complete,
    }

    if complete:
        status = "research_ready" if check_profile_ready(plan_id)["ready"] else "profile_complete"
        update_plan_status(plan_id, status)
        result["message"] = "Profile saved successfully."
        result["summary"] = profile_summary(profile)
        result["next_prompt"] = build_roadmap_prompt(plan_id, profile)
        result["profile_check"] = check_profile_ready(plan_id)

    return result
