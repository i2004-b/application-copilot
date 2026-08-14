# Application Copilot

A small multi-agent pipeline that fetches internship postings from public
job-board APIs, extracts structured requirements from each one, and matches
them against your resume — using both an open-source model (via Ollama) and
a closed-source model (Claude) so you have a real, measured answer to "why
did you pick this model for this step."

Built with LangGraph for orchestration and MCP so the same tools are
callable from Claude Desktop/Claude Code directly.

```
Scout (Greenhouse/Lever/Ashby APIs)
      |
      v
Extractor (Ollama, fallback to Claude)  -->  structured ExtractedJob
      |
      v
Matcher (sentence-transformers + cosine similarity)  -->  ranked resume bullets
      |
      v
SQLite  -->  Streamlit dashboard  /  MCP server
```

## 0. Setup (30 min)

```bash
cd application-copilot
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY at minimum
```

Optional but recommended for the open-vs-closed comparison: install
[Ollama](https://ollama.com), then `ollama pull llama3.1` (or `qwen2.5:7b`
— either runs fine on an M-series Mac).

Sanity check that everything imports and the sample UI runs, with **zero
API keys needed**:

```bash
streamlit run src/dashboard/app.py
```

You should see three sample postings from `data/sample_postings.json`,
filterable by role type. That's your "does the skeleton work" checkpoint
before you touch any model code.

## Week 1 — Data pipeline + first model comparison

**Goal by end of week:** real postings flowing in from at least one job
board, extracted into structured fields by both models, with a first
accuracy/cost/latency table.

1. [DONE]**Day 1–2 — Scout.** Pick 5–10 companies from your tracker that you know
   use Greenhouse (check if `boards.greenhouse.io/<company>` resolves).
   Run `src/scout/greenhouse.py` directly (`python -m src.scout.greenhouse`)
   against a real board token and confirm you get postings back. Then do
   the same for one Lever and one Ashby company in `lever.py` / `ashby.py` —
   they're stubbed with working request logic, you mostly need to test them
   against real board slugs and handle any response-shape surprises.

2. **Day 3 — Extractor, closed model.** Set `ANTHROPIC_API_KEY` in `.env`.
   Call `extract_with_claude()` on 10 real postings you pulled in step 1.
   Read the `ExtractedJob` outputs by hand — are `role_type` and
   `required_skills` actually right? Fix `schemas.py`'s field descriptions
   if the model is consistently misreading something.

3. **Day 4 — Extractor, open model.** With Ollama running, call
   `extract_with_ollama()` on the *same* 10 postings. Expect it to fail
   schema validation more often than Claude — that's the real finding, not
   a bug to hide. Add basic retry logic if you want, 

4. **Day 5 — Build the comparison table.** Hand-label the "correct" answer
   for each of your 10 postings. Write a short script (`scripts/compare_models.py`
   — not scaffolded, build it yourself, it's ~30 lines) that runs both
   extractors over the same postings and reports:
   - accuracy against your hand labels
   - average latency
   - total tokens / estimated $ cost (Claude's `response.usage` gives you
     this directly; Ollama is free but report tokens anyway for the
     comparison)

   This table is one of the most concrete artifacts in your whole
   portfolio — it goes straight into this README when you're done.


| Model | Exact Field Accuracy | Required Skill F1 | Preferred Skill F1 | Schema Validity | Avg Latency | Input Tokens | Output Tokens | Est. Cost |
|------ |---------------------:|------------------:|-------------------:|----------------:|------------:|-------------:|--------------:|----------:|
| Claude Haiku 4.5 | 68.0% | 0.000 | 0.100 | 10/10 | 5.21s | 29624 | 1567 | $0.0375 |
| Qwen 2.5 7B | 78.0% | 0.456 | 0.466 | 10/10 | 7.21s | 20822 | 1476 | $0.0000 |

## Week 2 — Matching, orchestration, and MCP

**Goal by end of week:** the full Scout → Extract → Match pipeline runs as
one LangGraph graph, and the same tools are callable from an MCP client.

1. **Day 6 — Your real resume bullets.** Replace
   `data/resume_bullets.example.json` with your actual bullets, tagged by
   which of your 3 resume tracks each one belongs to. Aim for 15–25
   bullets total so the matcher has something real to rank.

2. **Day 7 — Matcher.** Run `src/matcher/match.py`'s `match_job_to_resume()`
   against a few of the `ExtractedJob`s from week 1. Confirm the `track`
   filter in `resume_store.py` is actually pulling from the right subset —
   an "AI/ML Engineer" posting shouldn't surface your TPM/PM bullets.

3. **Day 8 — Wire the graph.** `src/graph/pipeline.py` already wires
   extract → match with an Ollama-first, Claude-fallback strategy. Run it
   (`python -m src.graph.pipeline`) with a real posting's text. Once that
   works, run `scripts/run_pipeline.py --board-token <token>` to push a
   whole company's postings through end to end and into SQLite
   (`python -m scripts.init_db` first, once).

4. **Day 9 — MCP server.** Start `src/mcp_server/server.py`
   (`python -m src.mcp_server.server`). Add it to your MCP client's config
   (Claude Desktop's `claude_desktop_config.json`, or Claude Code) and ask
   it to fetch and match postings using only your tools. This is the part
   worth recording a short demo clip of — "here's Claude using tools I
   built" is a strong thing to have on hand for an interview.

## Week 3 — Dashboard, eval, polish

**Goal by end of week:** a working, deployed demo and a README (this one,
or your top-level one) with real numbers in it.

1. **Day 1–2.** Point `src/dashboard/app.py` at real data instead of the
   sample file — swap `load_sample_postings()` for
   `db.models.all_postings_with_matches()`. Add the matched-bullets display
   the current TODO placeholder is standing in for.

2. **Day 3.** Run the pipeline across all the companies you set up in
   week 1, not just one. Note failure cases (a board with a nonstandard
   HTML structure, a model hallucinating a skill) — these are good "what I'd
   improve" talking points, not things to hide.

3. **Day 4.** Deploy the dashboard (Streamlit Community Cloud is the
   fastest path) so you have a live link, not just "clone and run it."

4. **Day 5.** Write up: architecture diagram (the one at the top of this
   file is a starting point), your model-comparison table from week 1, and
   a "what I'd build next" section (A2A between agents, more job boards,
   fine-tuning the extractor — pick one or two, don't list everything).

## Resume-bullet cheat sheet

Once this is built, here's roughly how to phrase it per track (fill in
your real numbers from the week 1 comparison table):

- **SWE/AI Engineer:** "Built a 3-agent LangGraph pipeline with a custom
  MCP server ingesting postings from N job-board APIs, extracting
  structured requirements and serving ranked matches through a Streamlit
  app."
- **AI/ML Engineer:** "Benchmarked an open-source model (Llama 3.1 via
  Ollama) against Claude on structured-extraction accuracy, latency, and
  cost across N postings, finding [X]% accuracy at [Y]x lower cost."
- **TPM/PM:** "Scoped and delivered a multi-agent system end to end in 3
  weeks — sequenced a data-pipeline-first build, and made the open- vs.
  closed-source model tradeoff call based on measured cost/accuracy data."

## Known gaps in this starter (by design)

- No retry/backoff on the API clients — add it if you hit rate limits.
- The Ollama extractor's JSON-repair story is minimal. Improving it is a
  legitimate week 2 stretch goal, not something you missed.
- No auth on the MCP server — fine for local personal use, not for sharing
  publicly as-is.
  