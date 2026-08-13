"""
Exposes the copilot's core functions as MCP tools so any MCP client
(Claude Desktop, Claude Code, etc.) can call them directly instead of you
running scripts by hand.

Week 2 task: once this runs locally, add it to your MCP client's config
(e.g. Claude Desktop's claude_desktop_config.json) and try asking it
something like "fetch Stripe's Greenhouse postings and match the
internship ones to my resume" using only these tools.

Run with: python -m src.mcp_server.server

Note: the Python MCP SDK's high-level server class was renamed from
`FastMCP` to `MCPServer` (moved from `mcp.server.fastmcp` to
`mcp.server`) in a package update -- if you find older tutorials/blog
posts referencing `FastMCP`, this is the same thing under
`pip install mcp`'s current API. The decorator-based `.tool()` /
`.resource()` / `.run()` usage is unchanged.
"""
from __future__ import annotations

from mcp.server import MCPServer

from src.scout.greenhouse import fetch_postings as fetch_greenhouse_postings
from src.scout.greenhouse import filter_by_keywords
from src.extractor.extract import extract_with_claude
from src.extractor.extract import extract_with_ollama
from src.matcher.match import match_job_to_resume

mcp = MCPServer("application-copilot")


@mcp.tool()
def fetch_postings(board_token: str, keyword_filter: str = "intern") -> list[dict]:
    """Fetch a company's open Greenhouse postings, optionally filtered by
    a title keyword (default: 'intern')."""
    postings = fetch_greenhouse_postings(board_token)
    if keyword_filter:
        postings = filter_by_keywords(postings, [keyword_filter])
    return [
        {"id": p["id"], "title": p["title"], "content": p.get("content", "")}
        for p in postings
    ]


@mcp.tool()
def extract_job_fields(raw_jd_text: str, company: str, title: str) -> dict:
    """Extract structured fields (role type, required skills, years of
    experience) from raw job-posting text."""
    try:
        result = extract_with_ollama(raw_jd_text, company=company, title=title)
    except Exception:
        result = extract_with_claude(raw_jd_text, company=company, title=title)

    return result.job.model_dump()


@mcp.tool()
def match_to_resume(extracted_job: dict) -> list[dict]:
    """Score an already-extracted job posting against your resume bullets
    and return the top matches with similarity scores."""
    return match_job_to_resume(extracted_job)


if __name__ == "__main__":
    mcp.run()
