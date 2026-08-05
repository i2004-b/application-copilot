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
    role_type: RoleType
    required_skills: list[str] = Field(
        default_factory=list,
        description="Short skill/tech keywords, e.g. ['Python', 'PyTorch', 'SQL']",
    )
    min_years_experience: Optional[int] = None
    location: Optional[str] = None
    is_internship: bool = True
    summary: str = Field(description="1-2 sentence plain-English summary of the role")
