"""
Requires sentence-transformers to actually download its model on first
run, so this needs network access the first time you run it (results are
then cached locally). Skipped gracefully if that download isn't possible
in your environment.
"""
import pytest

from src.matcher.resume_store import ResumeStore


def test_top_matches_returns_k_results():
    try:
        store = ResumeStore("data/resume_bullets.example.json")
    except Exception as exc:  # model download blocked, etc.
        pytest.skip(f"Could not load embedding model: {exc}")

    results = store.top_matches("Python backend engineering internship", k=3)
    assert len(results) == 3
    assert all("score" in r for r in results)


def test_track_filter_narrows_results():
    try:
        store = ResumeStore("data/resume_bullets.example.json")
    except Exception as exc:
        pytest.skip(f"Could not load embedding model: {exc}")

    results = store.top_matches("product roadmap", k=5, track="TPM/PM")
    assert all("TPM/PM" in r["tracks"] for r in results)
