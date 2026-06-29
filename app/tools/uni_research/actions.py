"""GROUP D — University research workflow tools."""

import json
from typing import Literal

from fastmcp import FastMCP
from fastmcp.apps.config import AppConfig

from app.services.profile import get_profile
from app.services.profile_validation import check_profile_ready
from app.services.scoring import generate_candidate_score, match_score
from app.services.university import (
    add_university,
    compare_universities as fetch_universities_for_compare,
    get_university,
    list_universities,
    remove_university as delete_university,
)
from app.tools.constants import WIDGET_URIS
from app.tools.uni_research.prompts import LOOKUP_BRIEF, RESEARCH_PROMPT_TEMPLATE, TIER_RULES


def register(mcp: FastMCP) -> None:
    @mcp.tool
    def search_universities(
        plan_id: int,
        target_degree: Literal["MS", "PhD", "MBA", "MEng", "MRes", "LLM", "other"] = "MS",
        target_field: str = "",
        preferred_countries: list[str] | None = None,
        max_results_per_tier: int = 5,
        require_funding: bool = False,
        require_post_study_work: bool = False,
    ) -> dict:
        """Run profile-weighted university search brief for host AI. Aliases: find_unis, search, research_unis."""
        validation = check_profile_ready(plan_id)
        if not validation["ready"]:
            return {
                "status": "blocked",
                "missing_fields": validation["missing_fields"],
                "profile_completeness": validation["profile_completeness"],
            }

        profile = get_profile(plan_id) or {}
        scores = profile.get("candidate_score") or generate_candidate_score(profile)
        profile_json = json.dumps(profile, indent=2, default=str)

        return {
            "status": "ready",
            "plan_id": plan_id,
            "candidate_score": scores,
            "profile": profile,
            "search_params": {
                "target_degree": target_degree or profile.get("target_degree"),
                "target_field": target_field or profile.get("target_field") or profile.get("major"),
                "preferred_countries": preferred_countries or profile.get("preferred_countries") or [profile.get("region")],
                "max_results_per_tier": max_results_per_tier,
                "require_funding": require_funding,
                "require_post_study_work": require_post_study_work,
            },
            "research_prompt": RESEARCH_PROMPT_TEMPLATE.format(profile_json=profile_json),
            "tier_rules": TIER_RULES,
            "next_steps": [
                "Research 3-4 REACH, 4-5 TARGET, 3-4 SAFETY programs using research_prompt",
                "For each result call add_university_to_plan with category and metadata",
                "Then call show_university_basket",
            ],
        }

    @mcp.tool
    def match_universities(
        plan_id: int,
        university_name: str,
        program_name: str = "",
        median_gpa: float = 3.5,
        min_gpa: float = 3.0,
        ielts_min: float = 6.5,
        annual_tuition: float = 0,
        has_funding: bool = False,
        country: str = "",
        campus_type: str = "",
        post_study_visa_available: bool = True,
    ) -> dict:
        """Score profile vs program requirements. Aliases: match, fit_check."""
        profile = get_profile(plan_id) or {}
        program = {
            "university_name": university_name,
            "program_name": program_name,
            "median_gpa": median_gpa,
            "min_gpa": min_gpa,
            "ielts_min": ielts_min,
            "annual_tuition": annual_tuition,
            "tuition_usd": annual_tuition,
            "has_funding": has_funding,
            "country": country,
            "campus_type": campus_type,
            "post_study_visa_available": post_study_visa_available,
        }
        result = match_score(profile, program)
        return {"plan_id": plan_id, "university_name": university_name, "program_name": program_name, **result}

    @mcp.tool
    def get_university_detail(university_id: int) -> dict:
        """Full details for a shortlisted university. Alias: uni_info, uni_detail."""
        uni = get_university(university_id)
        if uni:
            return uni
        return {"error": f"University {university_id} not found", "lookup_brief": LOOKUP_BRIEF}

    @mcp.tool
    def get_program_detail(university_name: str, program_name: str) -> dict:
        """Lookup brief for a specific program — host AI researches then saves via add_university_to_plan."""
        return {
            "university_name": university_name,
            "program_name": program_name,
            "lookup_brief": LOOKUP_BRIEF,
            "fields_to_research": [
                "qs_rank", "subject_rank", "acceptance_rate", "median_gpa",
                "ielts_min", "tuition_usd", "deadline", "funding_notes", "faculty_alignment",
            ],
        }

    @mcp.tool
    def compare_universities(university_ids: list[int]) -> dict:
        """Side-by-side comparison of 2–5 shortlisted universities. Aliases: compare, compare_unis."""
        items = fetch_universities_for_compare(university_ids)
        return {"universities": items, "count": len(items)}

    @mcp.tool
    def add_university_to_plan(
        plan_id: int,
        university_name: str,
        category: str = "target",
        program_name: str | None = None,
        degree_type: str | None = None,
        country: str | None = None,
        qs_rank: int | None = None,
        subject_rank: int | None = None,
        acceptance_rate: float | None = None,
        tuition_usd: float | None = None,
        deadline: str | None = None,
        funding_notes: str | None = None,
        match_score_val: float | None = None,
        risk_note: str | None = None,
    ) -> dict:
        """Add to shortlist with reach/target/safety category. Aliases: shortlist, add_uni."""
        extra = {
            k: v
            for k, v in {
                "program_name": program_name,
                "degree_type": degree_type,
                "country": country,
                "qs_rank": qs_rank,
                "subject_rank": subject_rank,
                "acceptance_rate": acceptance_rate,
                "tuition_usd": tuition_usd,
                "deadline": deadline,
                "funding_notes": funding_notes,
                "match_score": match_score_val,
                "risk_note": risk_note,
            }.items()
            if v is not None
        }
        return add_university(plan_id, university_name, category, **extra)

    @mcp.tool
    def remove_university(university_id: int) -> dict:
        """Remove from shortlist. Aliases: remove_uni, drop_uni."""
        ok = delete_university(university_id)
        return {"removed": ok, "university_id": university_id}

    @mcp.tool
    def get_universities(plan_id: int) -> list[dict]:
        """List shortlisted universities. Aliases: my_list, shortlist_view."""
        return list_universities(plan_id)

    @mcp.tool(app=AppConfig(resource_uri=WIDGET_URIS["university_basket"]))
    def show_university_basket(plan_id: int) -> dict:
        """Grouped reach/target/safety widget with Notify buttons. Aliases: basket, my_basket."""
        from app.services.college_subscriptions import list_subscriptions
        from app.services.profile import get_profile
        from app.services.study_plan import get_plan

        profile = get_profile(plan_id) or {}
        plan = get_plan(plan_id)
        subscriptions = list_subscriptions(plan["user_id"]) if plan else []
        subscribed_ids = {s["university_id"] for s in subscriptions}
        candidate = profile.get("candidate_score_json") or {}
        if isinstance(candidate, str):
            import json

            try:
                candidate = json.loads(candidate)
            except Exception:
                candidate = {}

        return {
            "plan_id": plan_id,
            "universities": list_universities(plan_id),
            "profile": profile,
            "candidate_score": candidate,
            "subscribed_university_ids": list(subscribed_ids),
            "subscription_count": len(subscriptions),
            "max_subscriptions": 10,
        }
