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




class ExtractedJobDetails(BaseModel):
    """Fields inferred by the LLM."""

    organization: Optional[str] = Field(
        description=(
            "A specifically named sub-brand, subsidiary, division, business unit, "
            "or product organization within the employer that the role belongs to. "
            "For example, if the employer is Stripe and the role is specifically "
            "at Bridge, return 'Bridge'. "
            "Do not return generic functional team names such as 'Engineering', "
            "'Account Management', or 'Sales' unless they are explicitly presented "
            "as a named organization. "
            "Return null if no distinct organization is identified."
        )
    )
    # Add descriptions of the role type for the LLM to get help in deciphering roles
    role_type: RoleType = Field(
        description=(
            "Classify the role according to its PRIMARY JOB FUNCTION, "
            "not the industry of the employer or whether the role interacts "
            "with technology. "
            "SWE = roles primarily responsible for designing, implementing, "
            "testing, or maintaining software. "
            "AI/ML Engineer = engineering roles primarily responsible for building, "
            "deploying, or maintaining AI/ML systems. "
            "AI/ML Researcher = roles primarily responsible for conducting AI/ML "
            "research or developing novel ML methods. "
            "TPM/PM = roles primarily responsible for managing technical programs, "
            "products, roadmaps, requirements, prioritization, delivery, or engineering "
            "execution. This includes technical program managers, product managers, "
            "and technical product managers. "
            "Other = roles outside these categories, including sales, account "
            "management, customer success, finance, marketing, HR, consulting, "
            "and operations. "
            "Classify based on what the employee is primarily hired to do. "
            "Do not classify a role as TPM/PM merely because it works with technology, "
            "engineers, products, or cross-functional stakeholders."
        )
    )

    required_skills: list[str] = Field(
        default_factory=list,
        description=(
            "Skills, technologies, tools, or competencies explicitly required "
            "by the posting. Return concise canonical skill names, preferably "
            "1-4 words each. Do not copy full phrases or sentences from the job "
            "description. Do not include preferred qualifications or inferred skills. "
            "Return an empty list if none are stated."
        )
    )

    preferred_skills: list[str] = Field(
        default_factory=list,
        description=(
            "Skills, technologies, tools, or competencies explicitly listed as "
            "preferred, desired, bonus, or nice-to-have. Return concise canonical "
            "skill names, preferably 1-4 words each. Do not copy full phrases or "
            "sentences. Return an empty list if none are stated."
        )
    )

    min_years_experience: Optional[int] = Field(
        default=None,
        description=(
            "Minimum overall years of professional experience explicitly required "
            "for the role. If several minimum experience requirements are listed, "
            "return the highest applicable overall threshold. Use null if no numeric "
            "minimum is stated. Do not infer years of experience."
        )
    )
    location: Optional[str] = Field(
        description=(
            "Primary work location explicitly stated in the job posting. "
            "Return a concise location such as 'London', 'New York, NY', "
            "'San Francisco, CA', or 'Remote'. "
            "If multiple locations are explicitly allowed, include them concisely. "
            "If the posting is remote, return 'Remote' rather than a boolean. "
            "Return null if no work location is stated."
        )
    )
    # Set based on keywords
    is_internship: bool = Field(
        description=(
            "True only if the posting explicitly describes an internship, intern, co-op, or comparable student work placement. Otherwise, false."
        )
    )
    summary: str = Field(description="1-2 sentence plain-English summary of the role")


class ExtractedJob(ExtractedJobDetails):
    """
    Complete normalized job after combining metadata with LLM-extracted details.
    """

    company: str
    title: str
