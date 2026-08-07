"""
Scout: Greenhouse job board client.

Greenhouse exposes a public, unauthenticated JSON API for any company's
careers page built on their platform:

    GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true

`board_token` is the slug in the company's Greenhouse URL, e.g. for
boards.greenhouse.io/stripe it's "stripe". You don't need an API key for
this -- it's the same data their public careers page renders from.

Week 1 task: call fetch_postings() for 5-10 companies from your tracker
that use Greenhouse, and print how many postings come back.
"""
from __future__ import annotations

import requests

GREENHOUSE_BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


def fetch_postings(board_token: str, timeout: int = 15) -> list[dict]:
    """
    Return the raw list of job postings for a company's Greenhouse board.

    Each posting dict includes at least: id, title, location, content
    (the full HTML job description), and absolute_url.
    """
    url = f"{GREENHOUSE_BASE_URL}/{board_token}/jobs"
    resp = requests.get(url, params={"content": "true"}, timeout=timeout)
    resp.raise_for_status()
    return resp.json().get("jobs", [])


def filter_by_keywords(postings: list[dict], keywords: list[str]) -> list[dict]:
    """
    Cheap pre-filter before you spend model tokens on extraction: keep only
    postings whose title contains one of the given keywords (case-insensitive).
    Useful for narrowing 500 postings down to the ~10 that mention "intern",
    "new grad", "AI", "ML", "product manager", etc.
    """
    keywords_lower = [k.lower() for k in keywords]
    return [
        p for p in postings
        if any(k in p.get("title", "").lower() for k in keywords_lower)
    ]


if __name__ == "__main__":
    # Quick manual smoke test -- swap in a real board token from your tracker.
    # Manual testing being done
    company = "anthropic"
    postings = fetch_postings(company)
    interns = filter_by_keywords(postings, ["intern"])
    print(f"{company.upper()}:")
    print(f"{len(postings)} total postings, {len(interns)} match 'intern'")
    for p in interns[:5]:
        print(f"- {p['title']} ({p['location']})")