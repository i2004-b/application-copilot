"""
Streamlit dashboard: browse matched postings and their best resume bullets.

Runs immediately against data/sample_postings.json with zero API keys, so
you can see the shape of the UI before any of the agent logic is wired up.

  streamlit run src/dashboard/app.py

Week 3 task: swap load_sample_postings() for db.models.all_postings_with_matches()
once postings are actually flowing through the real pipeline and landing in
data/copilot.db.
"""
import json
from pathlib import Path

import streamlit as st

SAMPLE_POSTINGS_PATH = Path(__file__).resolve().parents[2] / "data" / "sample_postings.json"


def load_sample_postings() -> list[dict]:
    return json.loads(SAMPLE_POSTINGS_PATH.read_text())


def main() -> None:
    st.set_page_config(page_title="Application Copilot", layout="wide")
    st.title("Application Copilot")
    st.caption(
        "Postings pulled from Greenhouse/Lever/Ashby, extracted into structured "
        "fields, and matched against your resume bullets."
    )

    postings = load_sample_postings()

    role_types = sorted({p["extracted"]["role_type"] for p in postings})
    selected_types = st.multiselect("Filter by role type", role_types, default=role_types)

    for posting in postings:
        job = posting["extracted"]
        if job["role_type"] not in selected_types:
            continue

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{job['title']} -- {job['company']}")
                st.write(job["summary"])
                st.caption(
                    f"{job['role_type']} | {job.get('location', 'n/a')} | "
                    f"source: {posting['source']}"
                )
                st.write("**Required skills:** " + ", ".join(job["required_skills"]))
            with col2:
                st.metric("Min. years exp.", job.get("min_years_experience", 0))

            # TODO(week 3): replace this placeholder with real matches from
            # matcher.match.match_job_to_resume(job) once the pipeline has
            # actually run and stored matches in the DB.
            st.info(
                "Matched resume bullets will appear here once you wire this "
                "view up to src/db/models.py -- see the TODO in this file.",
                icon="🚧",
            )


if __name__ == "__main__":
    main()
