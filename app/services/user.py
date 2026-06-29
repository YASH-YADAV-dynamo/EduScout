import random
import secrets
import string

from app.query import users as q


def _make_public_id() -> str:
    for _ in range(10):
        candidate = f"ESC-{secrets.token_hex(3).upper()}"
        if not q.get_user_by_public_id(candidate):
            return candidate
    return f"ESC-{secrets.token_hex(4).upper()}"


def generate_esid(prefix: str | None = None) -> str:
    letters = prefix or "".join(random.choices(string.ascii_uppercase, k=2))
    count = q.count_users_with_esid_prefix(letters)
    return f"{letters}{str(count + 1).zfill(4)}"


def _ensure_esid(user_id: int) -> str:
    user = q.get_user_by_id(user_id)
    if user and user.get("esid"):
        return user["esid"]
    esid = generate_esid()
    q.update_user_esid(user_id, esid)
    return esid


def get_or_create_user(email: str, name: str) -> dict:
    row = q.get_user_by_email(email)
    if row:
        if not row.get("esid"):
            esid = generate_esid()
            q.update_user_esid(row["id"], esid)
            row["esid"] = esid
        return row
    public_id = _make_public_id()
    esid = generate_esid()
    return q.insert_user(email, name, public_id, esid)


def get_or_create_by_google(*, google_sub: str, email: str, name: str) -> dict:
    row = q.get_user_by_google_sub(google_sub)
    if row:
        if not row.get("esid"):
            esid = generate_esid()
            q.update_user_esid(row["id"], esid)
            row["esid"] = esid
        return row

    existing = q.get_user_by_email(email)
    if existing:
        q.update_user_google_sub(existing["id"], google_sub, name)
        if not existing.get("esid"):
            esid = generate_esid()
            q.update_user_esid(existing["id"], esid)
            existing["esid"] = esid
        existing["google_sub"] = google_sub
        existing["name"] = name
        return existing

    public_id = _make_public_id()
    esid = generate_esid()
    return q.insert_user(email, name, public_id, esid, google_sub=google_sub)


def get_user(user_id: int) -> dict | None:
    return q.get_user_by_id(user_id)


def get_user_by_public_id(public_id: str) -> dict | None:
    return q.get_user_by_public_id(public_id)


def get_user_by_esid(esid: str) -> dict | None:
    return q.get_user_by_esid(esid)


def get_user_by_plan(plan_id: int) -> dict | None:
    return q.get_user_by_plan_id(plan_id)


def update_overall_score(user_id: int, score: float) -> None:
    q.update_overall_score(user_id, score)


def ensure_public_id(user_id: int) -> str:
    user = q.get_user_by_id(user_id)
    if user and user.get("public_id"):
        return user["public_id"]
    public_id = _make_public_id()
    q.update_user_public_id(user_id, public_id)
    return public_id
