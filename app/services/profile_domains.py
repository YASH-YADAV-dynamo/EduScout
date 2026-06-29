from app.services.profile_extended import patch_profile


def save_academic(
    plan_id: int,
    *,
    degree: str | None = None,
    major: str | None = None,
    cgpa: float | None = None,
    university_name: str | None = None,
    institution_tier: str | None = None,
    target_degree: str | None = None,
    target_field: str | None = None,
    gpa_scale: str | None = None,
) -> dict:
    return patch_profile(
        plan_id,
        degree=degree,
        major=major,
        cgpa=cgpa,
        university_name=university_name,
        institution_tier=institution_tier,
        target_degree=target_degree,
        target_field=target_field,
        gpa_scale=gpa_scale,
    )


def save_exams(plan_id: int, exams: dict) -> dict:
    return patch_profile(plan_id, exams_json=exams)


def save_research(plan_id: int, research: dict) -> dict:
    return patch_profile(plan_id, research_json=research)


def save_work(plan_id: int, work: dict) -> dict:
    return patch_profile(plan_id, work_json=work)


def save_extracurriculars(plan_id: int, extras: dict) -> dict:
    return patch_profile(plan_id, extracurriculars_json=extras)


def save_finance(
    plan_id: int,
    *,
    budget_usd: float | None = None,
    living_budget_usd: float | None = None,
    scholarship_seeking: bool | None = None,
    funding_open: bool | None = None,
    budget_range: str | None = None,
) -> dict:
    return patch_profile(
        plan_id,
        budget_usd=budget_usd,
        living_budget_usd=living_budget_usd,
        scholarship_seeking=scholarship_seeking,
        funding_open=funding_open,
        budget_range=budget_range,
    )


def save_preferences(
    plan_id: int,
    *,
    preferred_countries: list | None = None,
    campus_type: str | None = None,
    campus_size: str | None = None,
    visa_constraints: str | None = None,
    post_study_goal: str | None = None,
    target_intake: str | None = None,
    intake_semester: str | None = None,
    region: str | None = None,
    priority: str | None = None,
) -> dict:
    fields = {
        "campus_type": campus_type,
        "campus_size": campus_size,
        "visa_constraints": visa_constraints,
        "post_study_goal": post_study_goal,
        "target_intake": target_intake,
        "intake_semester": intake_semester,
        "region": region,
        "priority": priority,
    }
    if preferred_countries is not None:
        fields["preferred_countries_json"] = preferred_countries
    return patch_profile(plan_id, **fields)
