from app.query import documents as q


def save_document(
    plan_id: int,
    doc_type: str,
    content: str,
    *,
    format: str = "markdown",
    target_university: str | None = None,
) -> dict:
    current_max = q.get_max_document_version(plan_id, doc_type, target_university)
    version = current_max + 1
    doc = q.insert_document(plan_id, doc_type, format, content, target_university, version)
    return doc


def get_latest_document(
    plan_id: int,
    doc_type: str,
    target_university: str | None = None,
) -> dict | None:
    return q.get_latest_document(plan_id, doc_type, target_university)


def list_documents(plan_id: int, doc_type: str | None = None) -> list[dict]:
    return q.list_documents(plan_id, doc_type)
