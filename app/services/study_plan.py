from app.query import study_plans as q


def create_plan(user_id: int, title: str) -> dict:
    return q.insert_plan(user_id, title)


def get_plan(plan_id: int) -> dict | None:
    return q.get_plan_by_id(plan_id)


def list_plans(user_id: int) -> list[dict]:
    return q.list_plans_by_user(user_id)


def update_plan_status(plan_id: int, status: str) -> dict | None:
    q.update_plan_status(plan_id, status)
    return get_plan(plan_id)
