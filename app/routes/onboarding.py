from typing import Any

from pydantic import BaseModel

from app.services.onboarding import save_onboarding, start_onboarding
from app.services.onboarding_submit import save_stage1, save_stage2, save_stage3, submit_all
from app.services.profile_validation import check_profile_ready as validate_profile_ready

from fastapi import APIRouter, Header

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


class StartRequest(BaseModel):
    region: str = "Europe"
    email: str | None = None
    name: str | None = None
    user_id: int | None = None
    plan_id: int | None = None


class Stage1Request(BaseModel):
    plan_id: int
    name: str | None = None
    degree: str | None = None
    major: str | None = None
    cgpa: float | None = None
    gpa_scale: str | None = None
    university_name: str | None = None
    institution_tier: str | None = None
    target_degree: str | None = None
    target_field: str | None = None
    preferred_countries: list[str] | None = None
    target_intake: str | None = None
    budget_usd: float | None = None
    living_budget_usd: float | None = None
    scholarship_seeking: bool | None = None
    budget_range: str | None = None
    region: str | None = None
    priority: str | None = None


class Stage2Request(BaseModel):
    plan_id: int
    exams: dict[str, Any] | None = None
    doc_outlines: dict[str, Any] | None = None


class Stage3Request(BaseModel):
    plan_id: int
    work: dict[str, Any] | None = None
    research: dict[str, Any] | None = None
    extracurriculars: dict[str, Any] | None = None
    campus_type: str | None = None
    campus_size: str | None = None
    visa_constraints: str | None = None
    post_study_goal: str | None = None
    funding_open: bool | None = None
    priority: str | None = None


class SubmitAllRequest(BaseModel):
    plan_id: int
    esid: str | None = None
    email: str | None = None
    stage1: dict[str, Any] | None = None
    stage2: dict[str, Any] | None = None
    stage3: dict[str, Any] | None = None


class SaveRequest(BaseModel):
    """Flat body shape sent by profile_form widget buildPayload()."""

    plan_id: int
    complete: bool = False
    degree: str | None = None
    major: str | None = None
    cgpa: float | None = None
    budget_range: str | None = None
    target_intake: str | None = None
    priority: str | None = None
    region: str | None = None
    target_degree: str | None = None
    target_field: str | None = None
    university_name: str | None = None
    institution_tier: str | None = None
    budget_usd: float | None = None
    preferred_countries: list[str] | None = None
    ielts_expected: float | None = None
    gre_taken: bool | None = None
    has_papers: bool | None = None
    full_time_months: int | None = None
    scholarship_seeking: bool | None = None
    campus_type: str | None = None
    post_study_goal: str | None = None


def _save_kwargs(body: SaveRequest) -> dict[str, Any]:
    return body.model_dump(exclude={"plan_id", "complete"}, exclude_none=True)


@router.get("/profile/{plan_id}")
def api_get_profile(plan_id: int):
    from app.services.onboarding_stages import get_stage_progress
    from app.services.profile import get_profile

    profile = get_profile(plan_id) or {}
    progress = get_stage_progress(plan_id)
    return {"plan_id": plan_id, "profile": profile, **progress}


@router.post("/start")
def api_start(body: StartRequest):
    return start_onboarding(
        plan_id=body.plan_id,
        user_id=body.user_id,
        email=body.email,
        name=body.name,
        region=body.region,
    )


@router.post("/stage1")
def api_stage1(body: Stage1Request, x_esid: str | None = Header(default=None)):
    return save_stage1(body.plan_id, body.model_dump(exclude_none=True))


@router.post("/stage2")
def api_stage2(body: Stage2Request, x_esid: str | None = Header(default=None)):
    data = body.model_dump(exclude_none=True)
    return save_stage2(body.plan_id, data)


@router.post("/stage3")
def api_stage3(body: Stage3Request, x_esid: str | None = Header(default=None)):
    return save_stage3(body.plan_id, body.model_dump(exclude_none=True))


@router.post("/submit_all")
def api_submit_all(body: SubmitAllRequest):
    return submit_all(
        body.plan_id,
        email=body.email,
        stage1=body.stage1,
        stage2=body.stage2,
        stage3=body.stage3,
    )


@router.post("/save")
def api_save(body: SaveRequest):
    return save_onboarding(body.plan_id, complete=body.complete, **_save_kwargs(body))


@router.post("/submit")
def api_submit(body: SaveRequest):
    result = save_onboarding(body.plan_id, complete=True, **_save_kwargs(body))
    if result.get("error"):
        return result
    ready = validate_profile_ready(body.plan_id)
    result["profile_check"] = ready
    result["instruction"] = (
        "Profile saved. Call check_profile_ready; fill gaps with collect_* tools; "
        "then generate_candidate_score and search_universities."
    )
    return result
