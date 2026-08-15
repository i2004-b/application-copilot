"""
Streamlit dashboard for browsing real job postings processed by the
Application Copilot pipeline and their best-matching resume bullets.

Run from the project root with:

    PYTHONPATH="$(pwd)" streamlit run src/dashboard/app.py
"""

import os
import sys
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Dashboard displays the frozen deployment snapshot rather than
# the development database used by the pipeline.
os.environ.setdefault(
    "DB_PATH",
    str(ROOT / "data" / "demo_copilot.db"),
)

from src.db.models import all_postings_with_matches


def main() -> None:
    st.set_page_config(
        page_title="Application Copilot",
        layout="wide",
    )

    st.title("Application Copilot")
    st.caption(
        "Job postings extracted into structured fields and matched "
        "against the most relevant resume bullets."
    )

    # Load real pipeline results from SQLite.
    postings = all_postings_with_matches()

    # Ignore any DB records that do not yet have extracted job data.
    postings = [
        p for p in postings
        if p.get("extracted") is not None
    ]

    if not postings:
        st.warning(
            "No processed postings found. Run the pipeline first to "
            "populate data/copilot.db."
        )
        return

    # Role-type filter.
    role_types = sorted(
        {
            p["extracted"]["role_type"]
            for p in postings
        }
    )

    selected_types = st.multiselect(
        "Filter by role type",
        role_types,
        default=role_types,
    )

    for posting in postings:
        job = posting["extracted"]

        if job["role_type"] not in selected_types:
            continue

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.subheader(
                    f"{job['title']} — {job['company']}"
                )

                st.write(job["summary"])

                st.caption(
                    f"{job['role_type']} | "
                    f"{job.get('location') or 'Location not specified'} | "
                    f"source: {posting['source']} | "
                    f"extractor: {posting.get('extraction_model', 'unknown')}"
                )

                required_skills = job.get("required_skills", [])

                if required_skills:
                    st.write(
                        "**Required skills:** "
                        + ", ".join(required_skills)
                    )
                else:
                    st.write("**Required skills:** None explicitly listed")

                preferred_skills = job.get("preferred_skills", [])

                if preferred_skills:
                    st.write(
                        "**Preferred skills:** "
                        + ", ".join(preferred_skills)
                    )

            with col2:
                min_years = job.get("min_years_experience")

                st.metric(
                    "Min. years exp.",
                    min_years if min_years is not None else "N/A",
                )

                st.metric(
                    "Resume matches",
                    len(posting["matches"]),
                )

            st.markdown("#### Top Resume Matches")

            matches = posting["matches"]

            if not matches:
                st.info(
                    "No resume matches were returned for this posting."
                )

            else:
                for i, match in enumerate(matches, start=1):
                    st.write(
                        f"**{i}. Similarity: "
                        f"{match['score']:.3f}**"
                    )
                    st.write(match["bullet_text"])


if __name__ == "__main__":
    main()