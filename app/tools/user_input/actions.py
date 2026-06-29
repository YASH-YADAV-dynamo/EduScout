"""GROUP B+C — Onboarding and deep profile intake tools."""

from typing import Literal

from fastmcp import FastMCP
from fastmcp.apps.config import AppConfig, ResourceCSP

from app.services.onboarding import save_onboarding, start_onboarding
from app.services.onboarding_stages import check_form_progress as get_form_progress
from app.services.onboarding_submit import save_stage1, save_stage2, save_stage3
from app.services.profile import get_profile
from app.services.user import get_user_by_plan
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
from app.services.profile_validation import check_profile_ready as validate_profile_ready
from app.services.scoring import generate_candidate_score
from app.services.session import resolve_current_user
from app.tools.constants import WIDGET_URIS
from app.tools.user_input.validation import REQUIRED_FOR_SEARCH  # noqa: F401 — re-export for docs


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        app=AppConfig(resource_uri=WIDGET_URIS["profile_form_stage1"], csp=ResourceCSP(connect_domains=["*"])),
    )
    def start_planning_widget(
        plan_id: int | None = None,
        user_id: int | None = None,
        email: str | None = None,
        name: str | None = None,
        region: str = "Europe",
    ) -> dict:
        """Launch Stage 1 profile form. Aliases: onboard, begin, start. Do NOT ask profile questions in chat."""
        if user_id is None:
            current = resolve_current_user()
            user_id = current["id"]
            email = email or current.get("email")
            if not name or name == "Student":
                name = current.get("name") or name
        return start_onboarding(
            plan_id=plan_id,
            user_id=user_id,
            email=email,
            name=name,
            region=region,
        )

    @mcp.tool
    def save_onboarding_step(
        plan_id: int,
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
        preferred_countries: list[str] | None = None,
        ielts_expected: float | None = None,
        gre_taken: bool | None = None,
        has_papers: bool | None = None,
        full_time_months: int | None = None,
        scholarship_seeking: bool | None = None,
        campus_type: str | None = None,
        post_study_goal: str | None = None,
    ) -> dict:
        """Persist each wizard step. Alias: save_step."""
        return save_onboarding(
            plan_id,
            complete=complete,
            degree=degree,
            major=major,
            cgpa=cgpa,
            budget_range=budget_range,
            target_intake=target_intake,
            priority=priority,
            region=region,
            target_degree=target_degree,
            target_field=target_field,
            university_name=university_name,
            institution_tier=institution_tier,
            budget_usd=budget_usd,
            preferred_countries=preferred_countries,
            ielts_expected=ielts_expected,
            gre_taken=gre_taken,
            has_papers=has_papers,
            full_time_months=full_time_months,
            scholarship_seeking=scholarship_seeking,
            campus_type=campus_type,
            post_study_goal=post_study_goal,
        )

    @mcp.tool
    def submit_onboarding(
        plan_id: int,
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
        preferred_countries: list[str] | None = None,
        ielts_expected: float | None = None,
        gre_taken: bool | None = None,
        has_papers: bool | None = None,
        full_time_months: int | None = None,
        scholarship_seeking: bool | None = None,
        campus_type: str | None = None,
        post_study_goal: str | None = None,
    ) -> dict:
        """Finalize onboarding and trigger roadmap workflow. Aliases: submit_profile, finish_onboarding."""
        result = save_onboarding(
            plan_id,
            complete=True,
            degree=degree,
            major=major,
            cgpa=cgpa,
            budget_range=budget_range,
            target_intake=target_intake,
            priority=priority,
            region=region,
            target_degree=target_degree,
            target_field=target_field,
            university_name=university_name,
            institution_tier=institution_tier,
            budget_usd=budget_usd,
            preferred_countries=preferred_countries,
            ielts_expected=ielts_expected,
            gre_taken=gre_taken,
            has_papers=has_papers,
            full_time_months=full_time_months,
            scholarship_seeking=scholarship_seeking,
            campus_type=campus_type,
            post_study_goal=post_study_goal,
        )
        if result.get("error"):
            return result
        ready = validate_profile_ready(plan_id)
        result["profile_check"] = ready
        result["instruction"] = (
            "Profile saved. Call check_profile_ready; fill gaps with collect_* tools; "
            "then generate_candidate_score and search_universities."
        )
        return result

    @mcp.tool(app=AppConfig(resource_uri=WIDGET_URIS["profile_form"]))
    def show_profile_widget(plan_id: int) -> dict:
        """Display filled profile as card. Alias: view_profile."""
        profile = get_profile(plan_id) or {"plan_id": plan_id}
        return {"plan_id": plan_id, "step": 0, "profile": profile, "region": profile.get("region")}

    @mcp.tool
    def collect_academic_profile(
        plan_id: int,
        degree: str | None = None,
        major: str | None = None,
        cgpa: float | None = None,
        university_name: str | None = None,
        institution_tier: Literal["top_50", "51_200", "201_500", "500_plus", "not_ranked"] | None = None,
        target_degree: str | None = None,
        target_field: str | None = None,
        gpa_scale: str | None = None,
    ) -> dict:
        """Collect academic foundation. Aliases: academics, grades."""
        profile = save_academic(
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
        ready = validate_profile_ready(plan_id)
        return {"saved": True, "profile": profile, **ready}

    @mcp.tool
    def collect_exam_scores(
        plan_id: int,
        ielts_taken: bool = False,
        ielts_overall: float = 0.0,
        ielts_listening: float = 0.0,
        ielts_reading: float = 0.0,
        ielts_writing: float = 0.0,
        ielts_speaking: float = 0.0,
        ielts_expected: float = 0.0,
        ielts_exam_date: str = "",
        toefl_taken: bool = False,
        toefl_total: int = 0,
        gre_taken: bool = False,
        gre_verbal: int = 0,
        gre_quant: int = 0,
        gre_awa: float = 0.0,
        gmat_taken: bool = False,
        gmat_total: int = 0,
        gmat_quant: int = 0,
        gmat_verbal: int = 0,
    ) -> dict:
        """Collect IELTS/TOEFL/GRE/GMAT actual or expected scores. Aliases: exams, scores, test_scores."""
        exams = {
            "ielts_taken": ielts_taken,
            "ielts_overall": ielts_overall,
            "ielts_listening": ielts_listening,
            "ielts_reading": ielts_reading,
            "ielts_writing": ielts_writing,
            "ielts_speaking": ielts_speaking,
            "ielts_expected": ielts_expected,
            "ielts_exam_date": ielts_exam_date,
            "toefl_taken": toefl_taken,
            "toefl_total": toefl_total,
            "gre_taken": gre_taken,
            "gre_verbal": gre_verbal,
            "gre_quant": gre_quant,
            "gre_awa": gre_awa,
            "gmat_taken": gmat_taken,
            "gmat_total": gmat_total,
            "gmat_quant": gmat_quant,
            "gmat_verbal": gmat_verbal,
        }
        profile = save_exams(plan_id, exams)
        ready = validate_profile_ready(plan_id)
        return {"saved": True, "profile": profile, **ready}

    @mcp.tool
    def collect_research_profile(
        plan_id: int,
        has_papers: bool = False,
        paper_count: int = 0,
        venue_type: Literal["journal", "conference", "workshop", "preprint", "none"] = "none",
        conference_tier: Literal["A*", "A", "B", "C", "unranked", "na"] = "na",
        authorship: Literal["first", "co-author", "contributor", "na"] = "na",
        is_peer_reviewed: bool = False,
        citation_count: int = 0,
        has_patent: bool = False,
        research_lab_months: int = 0,
        ongoing_thesis: bool = False,
        thesis_topic: str = "",
    ) -> dict:
        """Collect research background. Aliases: research, publications."""
        research = {
            "has_papers": has_papers,
            "paper_count": paper_count,
            "venue_type": venue_type,
            "conference_tier": conference_tier,
            "authorship": authorship,
            "is_peer_reviewed": is_peer_reviewed,
            "citation_count": citation_count,
            "has_patent": has_patent,
            "research_lab_months": research_lab_months,
            "ongoing_thesis": ongoing_thesis,
            "thesis_topic": thesis_topic,
        }
        profile = save_research(plan_id, research)
        ready = validate_profile_ready(plan_id)
        return {"saved": True, "profile": profile, **ready}

    @mcp.tool
    def collect_work_experience(
        plan_id: int,
        full_time_months: int = 0,
        internship_months: int = 0,
        current_role: str = "",
        current_company: str = "",
        employment_status: Literal["full_time", "part_time", "not_working", ""] = "",
        jobs_json: str = "",
        internships_json: str = "",
    ) -> dict:
        """Collect work and internship history. Aliases: work_exp, experience."""
        import json

        jobs = json.loads(jobs_json) if jobs_json else []
        internships = json.loads(internships_json) if internships_json else []
        if full_time_months and not jobs:
            jobs = [{"months": full_time_months, "role": current_role, "company": current_company}]
        if internship_months and not internships:
            internships = [{"months": internship_months}]
        work = {
            "jobs": jobs,
            "internships": internships,
            "employment_status": employment_status,
        }
        profile = save_work(plan_id, work)
        ready = validate_profile_ready(plan_id)
        return {"saved": True, "profile": profile, **ready}

    @mcp.tool
    def collect_extracurriculars(
        plan_id: int,
        leadership_roles: bool = False,
        competitions: str = "",
        awards: bool = False,
        open_source_or_projects: bool = False,
        volunteer_work: bool = False,
        details: str = "",
    ) -> dict:
        """Collect extracurriculars and leadership. Aliases: extras, activities."""
        extras = {
            "leadership_roles": leadership_roles,
            "competitions": competitions,
            "awards": awards,
            "open_source_or_projects": open_source_or_projects,
            "volunteer_work": volunteer_work,
            "details": details,
        }
        profile = save_extracurriculars(plan_id, extras)
        ready = validate_profile_ready(plan_id)
        return {"saved": True, "profile": profile, **ready}

    @mcp.tool
    def collect_financial_profile(
        plan_id: int,
        budget_usd: float = 0.0,
        living_budget_usd: float = 0.0,
        scholarship_seeking: bool = False,
        funding_open: bool = False,
        budget_range: str | None = None,
    ) -> dict:
        """Collect financial profile. Aliases: finances, budget."""
        profile = save_finance(
            plan_id,
            budget_usd=budget_usd or None,
            living_budget_usd=living_budget_usd or None,
            scholarship_seeking=scholarship_seeking,
            funding_open=funding_open,
            budget_range=budget_range,
        )
        ready = validate_profile_ready(plan_id)
        return {"saved": True, "profile": profile, **ready}

    @mcp.tool
    def collect_preferences(
        plan_id: int,
        preferred_countries: list[str] | None = None,
        campus_type: Literal["urban", "suburban", "rural", "no_preference", ""] = "",
        campus_size: Literal["large", "small", "no_preference", ""] = "",
        visa_constraints: str = "",
        post_study_goal: str = "",
        target_intake: str | None = None,
        intake_semester: str | None = None,
        region: str | None = None,
        priority: str | None = None,
    ) -> dict:
        """Collect location and preference constraints. Aliases: prefs, wishlist."""
        profile = save_preferences(
            plan_id,
            preferred_countries=preferred_countries,
            campus_type=campus_type or None,
            campus_size=campus_size or None,
            visa_constraints=visa_constraints or None,
            post_study_goal=post_study_goal or None,
            target_intake=target_intake,
            intake_semester=intake_semester,
            region=region,
            priority=priority,
        )
        ready = validate_profile_ready(plan_id)
        return {"saved": True, "profile": profile, **ready}

    @mcp.tool
    def generate_candidate_score(plan_id: int) -> dict:
        """Compute admit likelihood score per dimension. Aliases: score_me, evaluate_me."""
        profile = get_profile(plan_id) or {}
        scores = generate_candidate_score(profile)
        patch_profile(plan_id, candidate_score_json=scores)
        set_profile_completeness(plan_id, validate_profile_ready(plan_id)["profile_completeness"])
        return {"plan_id": plan_id, "candidate_score": scores, "profile": profile}

    @mcp.tool
    def check_profile_ready(plan_id: int) -> dict:
        """Verify Section 7 gates before university search."""
        return validate_profile_ready(plan_id)

    @mcp.tool
    def check_form_progress(plan_id: int) -> dict:
        """Return current onboarding stage (0–3) and whether profile is ready for search."""
        return get_form_progress(plan_id)

    @mcp.tool
    def handle_greeting(user_id: int | None = None, plan_id: int | None = None) -> dict:
        """Called on any opening message (hi, hello, I'm interested, etc.)."""
        if user_id is None:
            user_id = resolve_current_user()["id"]
        if plan_id is None:
            from app.services.study_plan import list_plans

            plans = list_plans(user_id)
            plan_id = plans[0]["id"] if plans else None
        if plan_id is None:
            started = start_onboarding(user_id=user_id)
            plan_id = started["plan_id"]
        progress = get_form_progress(plan_id)
        return {
            "plan_id": plan_id,
            "user_id": user_id,
            "form_stage": progress["stage_complete"],
            "instruction": "Show the appropriate stage widget immediately",
            **progress,
        }

    @mcp.tool(
        app=AppConfig(resource_uri=WIDGET_URIS["profile_form_stage2"], csp=ResourceCSP(connect_domains=["*"])),
    )
    def show_stage2_widget(plan_id: int) -> dict:
        """Open Stage 2 exam scores and document upload widget."""
        user = get_user_by_plan(plan_id)
        profile = get_profile(plan_id) or {}
        return {
            "plan_id": plan_id,
            "esid": user.get("esid") if user else None,
            "stage": 2,
            "profile": profile,
            "instruction": "User should upload resume/transcript and enter exam scores.",
        }

    @mcp.tool(
        app=AppConfig(resource_uri=WIDGET_URIS["profile_form_stage3"], csp=ResourceCSP(connect_domains=["*"])),
    )
    def show_stage3_widget(plan_id: int) -> dict:
        """Open Stage 3 experience and preferences widget."""
        user = get_user_by_plan(plan_id)
        profile = get_profile(plan_id) or {}
        return {
            "plan_id": plan_id,
            "esid": user.get("esid") if user else None,
            "email": user.get("email") if user else None,
            "stage": 3,
            "profile": profile,
        }

    @mcp.tool
    def save_onboarding_stage(plan_id: int, stage: int, data: dict | None = None) -> dict:
        """Persist onboarding stage data from widget submit."""
        payload = data or {}
        if stage == 1:
            return save_stage1(plan_id, payload)
        if stage == 2:
            return save_stage2(plan_id, payload)
        if stage == 3:
            return save_stage3(plan_id, payload)
        raise ValueError("stage must be 1, 2, or 3")
