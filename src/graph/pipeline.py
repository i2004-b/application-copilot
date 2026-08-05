"""
LangGraph orchestration: Scout output -> Extract -> Match, as one graph.

This is deliberately a straight line to start. Once it runs end to end,
the natural "week 2 stretch" extensions are:
  - a conditional edge that falls back to extract_with_claude() when
    extract_with_ollama() throws or fails schema validation
  - a second branch that runs draft_tailored_pitch() after match_node
  - per-node timing/token logging so your README table writes itself

Run it directly with `python -m src.graph.pipeline` once scout + extractor
+ matcher all work individually -- don't wire the graph before its pieces
work standalone, you'll waste time debugging the graph instead of the logic.
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph, END

from src.extractor.extract import extract_with_claude, extract_with_ollama
from src.matcher.match import match_job_to_resume


class PipelineState(TypedDict, total=False):
    raw_jd: str
    company: str
    extracted: dict
    extraction_model: str
    matches: list[dict]


def extract_node(state: PipelineState) -> PipelineState:
    try:
        result = extract_with_ollama(state["raw_jd"])
    except Exception:
        # Local model unavailable or produced invalid output -- fall back
        # to the closed-source model rather than losing the posting.
        result = extract_with_claude(state["raw_jd"])
    return {
        **state,
        "extracted": result.job.model_dump(),
        "extraction_model": result.model,
    }


def match_node(state: PipelineState) -> PipelineState:
    matches = match_job_to_resume(state["extracted"])
    return {**state, "matches": matches}


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("extract", extract_node)
    graph.add_node("match", match_node)
    graph.set_entry_point("extract")
    graph.add_edge("extract", "match")
    graph.add_edge("match", END)
    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke(
        {
            "raw_jd": (
                "We're looking for a Software Engineering Intern with experience "
                "in Python, distributed systems, and a strong CS fundamentals "
                "background. You'll work on our core API platform."
            ),
            "company": "Example Co",
        }
    )
    print(result)
