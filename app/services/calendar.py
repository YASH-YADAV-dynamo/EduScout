from app.query import calendar as q


def create_event(plan_id: int, event_id: str, title: str) -> dict:
    return q.insert_event(plan_id, event_id, title)


def list_events(plan_id: int) -> list[dict]:
    return q.list_events_for_plan(plan_id)
