from fastmcp import FastMCP

from app.services.study_plan import create_plan, get_plan, list_plans
from app.services.task import create_task, list_tasks, update_task_status
from app.services.calendar import create_event, list_events


def register(mcp: FastMCP) -> None:
    @mcp.tool
    def create_study_plan(user_id: int, title: str) -> dict:
        """Create a master study roadmap. Aliases: make_plan, plan."""
        return create_plan(user_id, title)

    @mcp.tool
    def get_study_plan(plan_id: int) -> dict:
        """Retrieve a study plan. Aliases: my_plan, roadmap."""
        plan = get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        return plan

    @mcp.tool
    def list_study_plans(user_id: int) -> list[dict]:
        """List all study plans for a user. Alias: all_plans."""
        return list_plans(user_id)

    @mcp.tool
    def add_task(plan_id: int, title: str, due_date: str | None = None) -> dict:
        """Add a task with optional due date (YYYY-MM-DD). Aliases: task, remind_me."""
        return create_task(plan_id, title, due_date)

    @mcp.tool
    def get_tasks(plan_id: int) -> list[dict]:
        """List tasks for a study plan. Aliases: tasks, todo, my_tasks."""
        return list_tasks(plan_id)

    @mcp.tool
    def complete_task(task_id: int) -> dict:
        """Mark a task complete. Aliases: done, tick, finish_task."""
        result = update_task_status(task_id, "completed")
        if not result:
            raise ValueError(f"Task {task_id} not found")
        return result

    @mcp.tool
    def add_calendar_event(plan_id: int, event_id: str, title: str) -> dict:
        """Add a deadline or event. Aliases: event, schedule."""
        return create_event(plan_id, event_id, title)

    @mcp.tool
    def get_calendar_events(plan_id: int) -> list[dict]:
        """List calendar events. Aliases: calendar, deadlines."""
        return list_events(plan_id)
