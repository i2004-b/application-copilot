"""
End-to-end pipeline runner for Greenhouse, Lever, and Ashby.

Examples:

python -m scripts.run_pipeline \
    --source greenhouse \
    --board-token stripe \
    --company "Stripe" \
    --keyword intern

python -m scripts.run_pipeline \
    --source ashby \
    --board-token openai \
    --company "OpenAI" \
    --keyword intern

python -m scripts.run_pipeline \
    --source lever \
    --board-token palantir \
    --company "Palantir" \
    --keyword intern
"""

from __future__ import annotations

import argparse
import html
import re

from src.db.models import init_db, save_posting, save_matches
from src.graph.pipeline import build_graph

from src.scout import greenhouse
from src.scout import lever
from src.scout import ashby


def strip_html(text: str) -> str:
    """Remove basic HTML tags from ATS text."""
    text = html.unescape(text or "")
    return re.sub(r"<[^>]+>", " ", text)


def normalize_posting(posting: dict, source: str) -> dict:
    """
    Convert Greenhouse, Lever, or Ashby postings into the same
    internal structure expected by the pipeline.
    """

    if source == "greenhouse":
        return {
            "title": posting.get("title", ""),
            "content": posting.get("content", ""),
        }

    if source == "ashby":
        return {
            "title": posting.get("title", ""),
            "content": posting.get("descriptionPlain", ""),
        }

    if source == "lever":
        parts = []

        description = posting.get("descriptionPlain")
        if description:
            parts.append(description)

        # Lever often stores qualifications/responsibilities
        # in separate list sections.
        for section in posting.get("lists", []):
            heading = section.get("text", "")
            body = strip_html(section.get("content", ""))

            if heading:
                parts.append(heading)

            if body:
                parts.append(body)

        additional = posting.get("additionalPlain")
        if additional:
            parts.append(additional)

        return {
            "title": posting.get("text", ""),
            "content": "\n\n".join(parts),
        }

    raise ValueError(f"Unsupported source: {source}")


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source",
        required=True,
        choices=["greenhouse", "lever", "ashby"],
        help="ATS source",
    )

    parser.add_argument(
        "--board-token",
        required=True,
        help="ATS board/company slug",
    )

    parser.add_argument(
        "--company",
        required=True,
        help="Human-readable company name",
    )

    parser.add_argument(
        "--keyword",
        default="intern",
        help="Filter job titles by keyword",
    )

    args = parser.parse_args()

    init_db()
    app = build_graph()

    # Pick the appropriate Scout.
    if args.source == "greenhouse":
        raw_postings = greenhouse.fetch_postings(args.board_token)
        raw_postings = greenhouse.filter_by_keywords(
            raw_postings,
            [args.keyword],
        )

    elif args.source == "lever":
        raw_postings = lever.fetch_postings(args.board_token)
        raw_postings = lever.filter_by_keywords(
            raw_postings,
            [args.keyword],
        )

    else:
        raw_postings = ashby.fetch_postings(args.board_token)
        raw_postings = ashby.filter_by_keywords(
            raw_postings,
            [args.keyword],
        )

    print(
        f"Fetched {len(raw_postings)} {args.source} postings "
        f"matching '{args.keyword}'"
    )

    for raw_posting in raw_postings:
        posting = normalize_posting(
            raw_posting,
            args.source,
        )

        result = app.invoke(
            {
                "raw_jd": posting["content"],
                "company": args.company,
                "title": posting["title"],
            }
        )

        posting_id = save_posting(
            company=args.company,
            source=args.source,
            raw_jd=posting["content"],
            extracted=result["extracted"],
            model=result["extraction_model"],
        )

        save_matches(
            posting_id,
            result["matches"],
        )

        print(
            f"Saved posting {posting_id}: "
            f"{result['extracted']['title']}"
        )


if __name__ == "__main__":
    main()