from app.query import tasks as q


def create_task(plan_id: int, title: str, due_date: str | None = None) -> dict:
    return q.insert_task(plan_id, title, due_date)


def list_tasks(plan_id: int) -> list[dict]:
    return q.list_tasks_by_plan(plan_id)


def update_task_status(task_id: int, status: str) -> dict | None:
    q.update_task_status(task_id, status)
    return q.get_task_by_id(task_id)


def get_upcoming_tasks(within_days: int = 7) -> list[dict]:
    return q.get_upcoming_tasks(within_days)


def get_overdue_tasks() -> list[dict]:
    return q.get_overdue_tasks()
