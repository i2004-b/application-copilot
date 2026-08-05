"""
End-to-end run: fetch real postings for a company, push each through the
LangGraph pipeline, and store results in the DB.

    python -m scripts.run_pipeline --board-token stripe --keyword intern

Week 2/3 task: this is your main entry point once the individual pieces
work. Loop it over every company in your tracker that uses Greenhouse (see
scripts/run_pipeline.py's board_token arg for how to plug in more sources
once lever.py / ashby.py are wired the same way).
"""
from __future__ import annotations

import argparse

from src.db.models import init_db, save_posting, save_matches
from src.graph.pipeline import build_graph
from src.scout.greenhouse import fetch_postings, filter_by_keywords


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board-token", required=True, help="Greenhouse board token, e.g. 'stripe'")
    parser.add_argument("--keyword", default="intern")
    args = parser.parse_args()

    init_db()
    app = build_graph()

    postings = filter_by_keywords(fetch_postings(args.board_token), [args.keyword])
    print(f"Fetched {len(postings)} postings matching '{args.keyword}'")

    for posting in postings:
        result = app.invoke({"raw_jd": posting.get("content", ""), "company": args.board_token})
        posting_id = save_posting(
            company=args.board_token,
            source="greenhouse",
            raw_jd=posting.get("content", ""),
            extracted=result["extracted"],
            model=result["extraction_model"],
        )
        save_matches(posting_id, result["matches"])
        print(f"Saved posting {posting_id}: {result['extracted']['title']}")


if __name__ == "__main__":
    main()
