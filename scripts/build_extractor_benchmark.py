"""
Build extractor benchmark json file
"""
from __future__ import annotations

import argparse
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

import requests


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    parser = _HTMLTextExtractor()
    parser.feed(html.unescape(value))
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def fetch_greenhouse(spec: dict) -> tuple[str, str]:
    url = (
        "https://boards-api.greenhouse.io/v1/boards/"
        f"{spec['board_token']}/jobs/{spec['job_id']}"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Keep the same kind of content your Greenhouse scout currently feeds
    # to the extractor: the posting body returned by the API.
    raw_text = data.get("content", "")
    return data.get("title", ""), raw_text


def fetch_lever(spec: dict) -> tuple[str, str]:
    url = (
        "https://api.lever.co/v0/postings/"
        f"{spec['site']}/{spec['posting_id']}"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    parts: list[str] = []

    description = data.get("descriptionPlain") or strip_html(data.get("description"))
    if description:
        parts.append(description)

    for section in data.get("lists", []):
        heading = section.get("text")
        if heading:
            parts.append(heading)

        section_text = strip_html(section.get("content"))
        if section_text:
            parts.append(section_text)

    additional = data.get("additionalPlain") or strip_html(data.get("additional"))
    if additional:
        parts.append(additional)

    raw_text = "\n\n".join(parts).strip()
    return data.get("text", ""), raw_text


def fetch_ashby(spec: dict, expected_title: str) -> tuple[str, str]:
    url = (
        "https://api.ashbyhq.com/posting-api/job-board/"
        f"{spec['board_name']}"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    posting_id = spec["posting_id"]
    jobs = data.get("jobs", [])

    # Ashby's public board API returns the current jobs as a list rather
    # than a single-posting endpoint. Match using the UUID in jobUrl first.
    matches = [
        job for job in jobs
        if posting_id in (job.get("jobUrl") or "")
    ]

    # Fallback to exact title if the URL format ever changes.
    if not matches:
        matches = [
            job for job in jobs
            if job.get("title") == expected_title
        ]

    if not matches:
        raise RuntimeError(
            f"Could not find Ashby posting {posting_id!r} "
            f"on board {spec['board_name']!r}."
        )

    job = matches[0]
    return job.get("title", ""), job.get("descriptionPlain", "") or ""


def fetch_case(case: dict) -> dict:
    ats = case["ats"]
    spec = case["fetch"]

    if ats == "greenhouse":
        live_title, raw_text = fetch_greenhouse(spec)
    elif ats == "lever":
        live_title, raw_text = fetch_lever(spec)
    elif ats == "ashby":
        live_title, raw_text = fetch_ashby(spec, case["title"])
    else:
        raise ValueError(f"Unsupported ATS: {ats}")

    if not raw_text.strip():
        raise RuntimeError(f"No raw text returned for {case['id']}")

    if live_title and live_title != case["title"]:
        print(
            f"WARNING: title changed for {case['id']!r}: "
            f"manifest={case['title']!r}, live={live_title!r}"
        )

    return {
        "id": case["id"],
        "ats": case["ats"],
        "source_url": case["source_url"],
        "company": case["company"],
        "title": case["title"],
        "raw_text": raw_text,
        "expected": case["expected"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default="data/extractor_benchmark_manifest.json",
    )
    parser.add_argument(
        "--output",
        default="data/extractor_benchmark.json",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    output_path = Path(args.output)

    with manifest_path.open(encoding="utf-8") as f:
        cases = json.load(f)

    built: list[dict] = []

    for index, case in enumerate(cases, start=1):
        print(
            f"[{index}/{len(cases)}] "
            f"{case['ats']}: {case['company']} — {case['title']}"
        )
        built.append(fetch_case(case))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(built, f, indent=2, ensure_ascii=False)

    print(
        f"\nCreated {output_path} with {len(built)} frozen benchmark cases."
    )


if __name__ == "__main__":
    main()