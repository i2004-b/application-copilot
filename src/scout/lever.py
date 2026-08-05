"""
Scout: Lever job board client.

Lever's public postings API:

    GET https://api.lever.co/v0/postings/{company}?mode=json

`company` is the slug from the company's Lever URL, e.g. jobs.lever.co/figma
-> "figma". No API key required.

TODO(week 1): mirror greenhouse.py's filter_by_keywords() usage here once
this is wired up, and add both sources to the same Scout run.
"""
from __future__ import annotations

import requests

LEVER_BASE_URL = "https://api.lever.co/v0/postings"


def fetch_postings(company: str, timeout: int = 15) -> list[dict]:
    """
    Return the raw list of postings for a company's Lever board.

    Each posting includes: id, text (title), categories (team/location/
    commitment), descriptionPlain, and hostedUrl.
    """
    url = f"{LEVER_BASE_URL}/{company}"
    resp = requests.get(url, params={"mode": "json"}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
