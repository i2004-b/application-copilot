"""
Schema-only tests -- no network, no API keys needed. Run with `pytest`.
These check that ExtractedJob behaves the way the rest of the pipeline
assumes, so a bad schema change fails fast instead of surfacing as a
confusing error three modules away.
"""
from src.extractor.schemas import ExtractedJob


def test_minimal_valid_job():
    job = ExtractedJob(
        company="Acme",
        title="SWE Intern",
        role_type="SWE",
        summary="Build things.",
    )
    assert job.required_skills == []
    assert job.is_internship is True


def test_role_type_rejects_invalid_value():
    import pytest

    with pytest.raises(Exception):
        ExtractedJob(
            company="Acme",
            title="SWE Intern",
            role_type="Not A Real Role",
            summary="Build things.",
        )
