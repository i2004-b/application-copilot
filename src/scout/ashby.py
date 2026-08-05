"""
Scout: Ashby job board client.

Ashby's public job board API:

    GET https://api.ashbyhq.com/posting-api/job-board/{job_board_name}

`job_board_name` is the slug from the company's Ashby URL, e.g.
jobs.ashbyhq.com/ramp -> "ramp". No API key required.

TODO(week 1): same shape as greenhouse.py/lever.py -- fetch_postings()
returning a list of raw posting dicts with at least a title and a
description field, so extractor/extract.py can treat all three sources
the same way.
"""
from __future__ import annotations

import requests

ASHBY_BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"


def fetch_postings(job_board_name: str, timeout: int = 15) -> list[dict]:
    url = f"{ASHBY_BASE_URL}/{job_board_name}"
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json().get("jobs", [])
