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




class ExtractedJob(BaseModel):
    company: str
    title: str
    # Add descriptions of the role type for the LLM to get help in deciphering roles
    role_type: RoleType = Field(
        description=(
            "Classify the role according to its PRIMARY JOB FUNCTION, "  # Need these spaces or concatenates with the next line
            "not the industry of the employer or whether the role interacts "
            "with technology. "
            "SWE = software engineering/development roles. "
            "AI/ML Engineer = engineering roles building or deploying ML/AI systems. "
            "AI/ML Researcher = research-focused AI/ML roles. "
            "TPM/PM = technical program management, product management, technology, Bridges business, engineering, and design to build tech products successfully "
            "technical product management, or closely related roles. "
            "Other = roles outside these categories, including sales, account "
            "management, finance, marketing, HR, consulting, and operations. "
            "Do not choose the closest category when the job clearly belongs outside "
            "the target categories; use Other."
        )
    )



    required_skills: list[str] = Field(
        default_factory=list,
        description=(
            "Skills, technologies, tools, or competencies explicitly required "
            "in the posting. Use concise canonical names. Include only requirements, "
            "not preferred qualifications, responsibilities, or skills merely inferred "
            "from the job description. "
        )
    )

    preferred_skills: list[str] = Field(
        default_factory=list,
        description=(
            "Skills, technologies, tools, or competencies explicitly listed "
            "as preferred, desired, or bonus qualifications."
            "These are preferred (or preferable) skills or qualifications. Skills, technologies, tools, or competencies that are not required "
            "in the posting but may be suggested or 'like to haves'. Use concise canonical names. These skills are not mandatory but make the "
            "candidate stand out."
        )
    )

    
    min_years_experience: Optional[int] = Field(
        default=None,
        description=(
            "Minimum overall years or professional experience explicitly required "
            "for the role. If several minimum experience requirements are listed, "
            "return the highest applicable overall threshold. Use null if no numeric "
            "minimum is stated. Do not infer years of experience."
        )
    )
    location: Optional[str] = None
    # Set based on keywords
    is_internship: bool = Field(
        description=(
            "True only if the posting explicitly describes an internship, intern, co-op, or comparable student work placement. Otherwise, false."
        )
    )
    summary: str = Field(description="1-2 sentence plain-English summary of the role")
