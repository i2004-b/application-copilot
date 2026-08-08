"""
The structured shape every job posting gets normalized into, regardless of
which board it came from or which model extracted it. Both extract_with_claude
and extract_with_ollama in extract.py must return one of these -- that's what
makes the open-vs-closed model comparison apples-to-apples.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

RoleType = Literal["SWE", "AI/ML Engineer", "AI/ML Researcher", "TPM/PM", "Other"]

# Add descriptions of the role type for the LLM to get help in deciphering roles
role_type: RoleType = Field(
    description=(
        "Classify the role into exactly one category."
        "SWE = software engineering/development roles. "
        "AI/ML Engineer = engineering roles building or deploying ML/AI systems. "
        "AI/ML Researcher = research-focused AI/ML roles. "
        "TPM/PM = technical program management, product management, "
        "technical product management, or closely related roles. "
        "Other = roles outside these categories, including sales, account "
        "management, finance, marketing, HR, consulting, and operations. "
        "Do not choose the closest category when the job clearly belongs outside "
        "the target categories; use Other."
    )
)


class ExtractedJob(BaseModel):
    company: str
    title: str
    role_type: RoleType
    required_skills: list[str] = Field(
        default_factory=list,
        description=(
            "Skills, technologies, tools, or competencies explicitly required "
            "in the posting. Use concise canonical names. Include only requirements, "
            "not preferred qualifications, responsibilities, or skills merely inferred "
            "from the job description."
        )
    )
    min_years_experience: Optional[int] = None
    location: Optional[str] = None
    # Set based on keywords
    is_internship: bool = Field(
        description=(
            "True only if the posting explicitly describes an internship, intern, co-op, or comparable student work placement. Otherwise, false."
        )
    )
    summary: str = Field(description="1-2 sentence plain-English summary of the role")
