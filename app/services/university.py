from typing import Any

from app.query import universities as q


def add_university(
    plan_id: int,
    university_name: str,
    category: str = "target",
    **extra: Any,
) -> dict:
    return q.insert_university(plan_id, university_name, category, extra)


def get_university(university_id: int) -> dict | None:
    return q.get_university_by_id(university_id)


def list_universities(plan_id: int) -> list[dict]:
    return q.list_universities_by_plan(plan_id)


def remove_university(university_id: int) -> bool:
    return q.delete_university(university_id)


def compare_universities(university_ids: list[int]) -> list[dict]:
    results = []
    for uid in university_ids[:5]:
        uni = get_university(uid)
        if uni:
            results.append(uni)
    return results
