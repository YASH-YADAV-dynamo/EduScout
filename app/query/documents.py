"""All Supabase queries for the `documents` table."""
from __future__ import annotations

from app.database.db import get_client


def get_max_document_version(
    plan_id: int, doc_type: str, target_university: str | None
) -> int:
    """Return the current max version for this plan+doc_type+target_university combo."""
    sb = get_client()
    q = sb.table("documents").select("version").eq("plan_id", plan_id).eq("doc_type", doc_type)
    if target_university:
        q = q.eq("target_university", target_university)
    else:
        q = q.is_("target_university", "null")
    resp = q.order("version", desc=True).limit(1).execute()
    return resp.data[0]["version"] if resp.data else 0


def insert_document(
    plan_id: int,
    doc_type: str,
    format: str,
    content: str,
    target_university: str | None,
    version: int,
) -> dict:
    sb = get_client()
    data = {
        "plan_id": plan_id,
        "doc_type": doc_type,
        "format": format,
        "content": content,
        "version": version,
    }
    if target_university:
        data["target_university"] = target_university
    resp = sb.table("documents").insert(data).execute()
    return resp.data[0]


def get_document_by_id(doc_id: int) -> dict | None:
    sb = get_client()
    resp = sb.table("documents").select("*").eq("id", doc_id).execute()
    return resp.data[0] if resp.data else None


def get_latest_document(
    plan_id: int, doc_type: str, target_university: str | None = None
) -> dict | None:
    sb = get_client()
    q = sb.table("documents").select("*").eq("plan_id", plan_id).eq("doc_type", doc_type)
    if target_university:
        q = q.eq("target_university", target_university)
    else:
        q = q.is_("target_university", "null")
    resp = q.order("version", desc=True).limit(1).execute()
    return resp.data[0] if resp.data else None


def list_documents(plan_id: int, doc_type: str | None = None) -> list[dict]:
    sb = get_client()
    q = sb.table("documents").select("*").eq("plan_id", plan_id)
    if doc_type:
        q = q.eq("doc_type", doc_type)
    resp = q.order("created_at", desc=True).execute()
    return resp.data or []
