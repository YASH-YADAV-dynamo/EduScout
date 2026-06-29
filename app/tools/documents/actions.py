"""GROUP E — Resume, SOP, LOR document tools."""

from typing import Literal

from fastmcp import FastMCP

from app.services.document_extractor import analyze_and_store
from app.services.documents import get_latest_document, list_documents, save_document as persist_document
from app.services.profile import get_profile
from app.tools.documents.prompts import LOR_BRIEF, RESUME_RULES, RESUME_SECTIONS, SOP_BRIEF


def register(mcp: FastMCP) -> None:
    @mcp.tool
    def generate_resume_draft(
        plan_id: int,
        format: Literal["markdown", "latex", "both"] = "both",
        target_role: str = "",
        target_university: str = "",
    ) -> dict:
        """Return resume generation brief for host AI. Aliases: make_resume, cv, build_cv."""
        profile = get_profile(plan_id) or {}
        return {
            "plan_id": plan_id,
            "format": format,
            "target_role": target_role,
            "target_university": target_university,
            "compulsory_sections": RESUME_SECTIONS,
            "rules": RESUME_RULES,
            "profile": profile,
            "instruction": (
                "Write the resume in the requested format(s), then call save_document "
                "with doc_type='resume' or update_resume_section to persist."
            ),
        }

    @mcp.tool
    def get_resume(plan_id: int, target_university: str | None = None) -> dict:
        """Retrieve latest resume draft. Aliases: my_resume, view_cv."""
        doc = get_latest_document(plan_id, "resume", target_university)
        if doc:
            return doc
        return {"plan_id": plan_id, "content": None, "message": "No resume saved yet. Call generate_resume_draft first."}

    @mcp.tool
    def update_resume_section(
        plan_id: int,
        section: str,
        content: str,
        format: Literal["markdown", "latex"] = "markdown",
    ) -> dict:
        """Patch a specific resume section and persist. Aliases: edit_resume, fix_resume."""
        existing = get_latest_document(plan_id, "resume")
        base = existing["content"] if existing else ""
        updated = f"{base}\n\n## {section}\n{content}".strip()
        return persist_document(plan_id, "resume", updated, format=format)

    @mcp.tool
    def generate_sop_outline(
        plan_id: int,
        university_name: str,
        program_name: str = "",
    ) -> dict:
        """SOP skeleton brief per university. Aliases: sop, statement, sop_draft."""
        profile = get_profile(plan_id) or {}
        return {
            "plan_id": plan_id,
            "university_name": university_name,
            "program_name": program_name,
            "profile": profile,
            "brief": SOP_BRIEF.format(university=university_name, program=program_name or "target program"),
            "instruction": "Write SOP outline then call save_document with doc_type='sop'.",
        }

    @mcp.tool
    def generate_lor_guide(
        plan_id: int,
        recommender_type: Literal["academic", "professional", "supervisor"] = "academic",
        recommender_name: str = "",
    ) -> dict:
        """LOR request template and talking points. Aliases: lor, recommendation."""
        profile = get_profile(plan_id) or {}
        return {
            "plan_id": plan_id,
            "recommender_type": recommender_type,
            "recommender_name": recommender_name,
            "profile": profile,
            "brief": LOR_BRIEF.format(recommender_type=recommender_type),
            "instruction": "Draft LOR guide then call save_document with doc_type='lor'.",
        }

    @mcp.tool
    def save_document(
        plan_id: int,
        doc_type: Literal["resume", "sop", "lor"],
        content: str,
        format: Literal["markdown", "latex"] = "markdown",
        target_university: str | None = None,
    ) -> dict:
        """Persist a document draft written by the host AI."""
        return persist_document(plan_id, doc_type, content, format=format, target_university=target_university)

    @mcp.tool
    async def analyze_document(
        plan_id: int,
        doc_type: Literal["resume", "transcript", "sop"],
        content: str,
        filename: str,
        mime_type: str = "application/pdf",
    ) -> dict:
        """Receive base64 file from ChatGPT, extract outline, save to profile."""
        return analyze_and_store(plan_id, doc_type, content, filename, mime_type)
