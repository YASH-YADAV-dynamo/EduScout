RESUME_SECTIONS = [
    "Contact Info",
    "Education",
    "Skills",
    "Projects",
    "Work Experience",
    "Research / Publications",
    "Extracurriculars / Leadership",
    "Awards",
]

RESUME_RULES = """
Resume format rules:
- Single page for MS applicants
- Two pages acceptable for PhD / MBA with 3+ years work exp
- ATS-friendly: no tables, no images, standard fonts
- Quantify everything: "Improved X by Y%" not "Worked on X"
- Work Experience: STAR method bullets
- Research: full citation with venue tier noted
"""

SOP_BRIEF = """
Generate a Statement of Purpose outline tailored to {university} / {program}.
Include: hook, academic background, research/work relevance, why this program,
why this university (specific faculty/courses), career goals, conclusion.
Angle should differ per university — do not reuse generic text.
"""

LOR_BRIEF = """
Generate a Letter of Recommendation request guide for {recommender_type} recommender.
Include: talking points tied to candidate profile, specific examples to mention,
submission deadline reminder, and polite request template email.
"""
