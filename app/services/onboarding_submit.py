import json

from app.services.onboarding_stages import check_form_progress, mark_stage_complete
from app.services.profile_domains import (
    save_academic,
    save_exams,
    save_extracurriculars,
    save_finance,
    save_preferences,
    save_research,
    save_work,
)
from app.services.profile_extended import patch_profile, set_profile_completeness
from app.services.profile_validation import check_profile_ready
from app.services.scoring import generate_candidate_score
from app.services.study_plan import get_plan, update_plan_status
from app.services.user import get_user_by_plan, update_overall_score


def save_stage1(plan_id: int, data: dict) -> dict:
    profile = save_academic(
        plan_id,
        degree=data.get("degree"),
        major=data.get("major"),
        cgpa=data.get("cgpa"),
        university_name=data.get("university_name"),
        institution_tier=data.get("institution_tier"),
        target_degree=data.get("target_degree"),
        target_field=data.get("target_field"),
        gpa_scale=data.get("gpa_scale"),
    )
    save_finance(
        plan_id,
        budget_usd=data.get("budget_usd"),
        living_budget_usd=data.get("living_budget_usd"),
        scholarship_seeking=data.get("scholarship_seeking"),
        budget_range=data.get("budget_range"),
    )
    save_preferences(
        plan_id,
        preferred_countries=data.get("preferred_countries"),
        target_intake=data.get("target_intake"),
        region=data.get("region"),
        priority=data.get("priority"),
    )
    if data.get("name"):
        patch_profile(plan_id, degree=data.get("degree"))
    progress = mark_stage_complete(plan_id, 1, data)
    return {"plan_id": plan_id, "profile": profile, **progress}


def save_stage2(plan_id: int, data: dict) -> dict:
    exams = data.get("exams") or data
    profile = save_exams(plan_id, exams if isinstance(exams, dict) else data)
    progress = mark_stage_complete(plan_id, 2, data)
    return {"plan_id": plan_id, "profile": profile, **progress}


def save_stage3(plan_id: int, data: dict) -> dict:
    if data.get("work"):
        save_work(plan_id, data["work"])
    if data.get("research"):
        save_research(plan_id, data["research"])
    if data.get("extracurriculars"):
        save_extracurriculars(plan_id, data["extracurriculars"])
    save_preferences(
        plan_id,
        campus_type=data.get("campus_type"),
        campus_size=data.get("campus_size"),
        visa_constraints=data.get("visa_constraints"),
        post_study_goal=data.get("post_study_goal"),
        priority=data.get("priority"),
    )
    patch_profile(plan_id, funding_open=data.get("funding_open"))
    profile = patch_profile(plan_id)
    progress = mark_stage_complete(plan_id, 3, data)
    return {"plan_id": plan_id, "profile": profile, **progress}


def submit_all(plan_id: int, email: str | None = None, stage1: dict | None = None, stage2: dict | None = None, stage3: dict | None = None) -> dict:
    if stage1:
        save_stage1(plan_id, stage1)
    if stage2:
        save_stage2(plan_id, stage2)
    if stage3:
        save_stage3(plan_id, stage3)

    progress = check_form_progress(plan_id)
    if progress["stage_complete"] < 3:
        return {
            "status": "error",
            "message": "All 3 stages must be complete before final submit",
            "stage_complete": progress["stage_complete"],
        }

    validation = check_profile_ready(plan_id)
    if not validation["ready"]:
        return {
            "status": "error",
            "missing_fields": validation["missing_fields"],
            "profile_completeness": validation["profile_completeness"],
        }

    from app.services.profile import get_profile

    profile = get_profile(plan_id) or {}
    scores = generate_candidate_score(profile)
    patch_profile(plan_id, candidate_score_json=scores, form_stage_complete=3)
    set_profile_completeness(plan_id, validation["profile_completeness"])

    user = get_user_by_plan(plan_id)
    if user:
        update_overall_score(user["id"], scores.get("overall", 0))

    update_plan_status(plan_id, "research_ready")

    return {
        "status": "success",
        "esid": user.get("esid") if user else None,
        "email": email or (user.get("email") if user else None),
        "profile_completeness": validation["profile_completeness"],
        "candidate_score": scores,
        "next_action": "show_universities",
    }
