"""
Matcher agent, part 2: given an ExtractedJob, produce (a) the best-fitting
resume bullets and (b) a tailored one-line pitch for that specific posting.
"""
from __future__ import annotations

from src.extractor.schemas import ExtractedJob
from src.matcher.resume_store import ResumeStore

_store: ResumeStore | None = None

# Role to resume track mapping
ROLE_TO_TRACK = {
    "SWE": "SWE/AI Engineer",
    "AI/ML Engineer": "SWE/AI Engineer",
    "AI/ML Researcher": "AI/ML Researcher",
    "TPM/PM": "TPM/PM",
    "Other": None,
}


def _get_store() -> ResumeStore:
    global _store
    if _store is None:
        _store = ResumeStore()
    return _store


def match_job_to_resume(extracted: dict | ExtractedJob, k: int = 5) -> list[dict]:
    """Score an extracted job against your resume bullets for its role_type."""
    job = extracted if isinstance(extracted, ExtractedJob) else ExtractedJob(**extracted)

    track = ROLE_TO_TRACK.get(job.role_type)

    if track is None:
        return []
    
    query = f"{job.summary} Skills: {', '.join(job.required_skills)}"
    return _get_store().top_matches(query, k=k, track=track)


def draft_tailored_pitch(job: ExtractedJob, top_bullet: dict) -> str:
    """
    TODO(week 2): call Claude (see extractor/extract.py for the client
    pattern) to rewrite `top_bullet['text']` so it explicitly echoes
    language from `job.summary` / `job.required_skills`. Keep it to one
    sentence -- this is meant to go straight into a cover-letter opener or
    an application's "why this role" field, not replace your resume bullet.
    """
    raise NotImplementedError("Wire this up once extract_with_claude is working end to end.")
