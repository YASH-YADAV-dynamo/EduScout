import json
from datetime import datetime, timezone

from app.query import onboarding_stages as q
from app.services.profile_extended import patch_profile


def record_stage_snapshot(plan_id: int, stage: int, data: dict | None = None) -> None:
    snapshot = json.dumps(data or {})
    now = datetime.now(timezone.utc).isoformat()
    q.upsert_stage(plan_id, stage, now, snapshot)


def mark_stage_complete(plan_id: int, stage: int, data: dict | None = None) -> dict:
    record_stage_snapshot(plan_id, stage, data)
    patch_profile(plan_id, form_stage_complete=stage)
    return get_stage_progress(plan_id)


def get_stage_progress(plan_id: int) -> dict:
    rows = q.list_stages_for_plan(plan_id)
    completed = {r["stage"] for r in rows if r["completed_at"]}
    stage_complete = 0
    for s in (1, 2, 3):
        if s in completed:
            stage_complete = s
        else:
            break
    return {
        "plan_id": plan_id,
        "stage_complete": stage_complete,
        "stages": {r["stage"]: r["completed_at"] for r in rows},
    }


def check_form_progress(plan_id: int) -> dict:
    from app.services.profile_validation import check_profile_ready

    progress = get_stage_progress(plan_id)
    profile_ready = progress["stage_complete"] >= 3
    validation = check_profile_ready(plan_id) if profile_ready else {"ready": False, "missing_fields": []}
    return {
        **progress,
        "profile_ready": profile_ready and validation.get("ready", False),
        "missing_fields": validation.get("missing_fields", []) if profile_ready else [],
        "next_stage": progress["stage_complete"] + 1 if progress["stage_complete"] < 3 else None,
    }
