"""GROUP A — Identity & Account tool schemas."""

from pydantic import BaseModel, Field


class ProfilePatch(BaseModel):
    degree: str | None = None
    major: str | None = None
    cgpa: float | None = None
    budget: float | None = None
    budget_range: str | None = None
    target_intake: str | None = None
    priority: str | None = None
    region: str | None = None
    resume_url: str | None = None
    target_degree: str | None = None
    target_field: str | None = None
