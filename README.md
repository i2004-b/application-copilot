# Application Copilot

Application Copilot is an AI-powered internship search and resume-matching pipeline that pulls live job postings from public ATS APIs, extracts structured requirements, and ranks the most relevant resume bullets for each role.

The project compares a locally hosted open-source model (**Qwen 2.5 7B via Ollama**) against a closed-source model (**Claude Haiku 4.5**) for structured job extraction, allowing model choice to be based on measured accuracy, reliability, latency, and cost rather than intuition.

The pipeline is orchestrated with **LangGraph**, persists results in **SQLite**, exposes its core capabilities as **MCP tools**, and presents processed postings through a deployed **Streamlit dashboard**.

**Live Dashboard:** https://application-copilot.streamlit.app/

**MCP Demo:** [Watch the Claude Desktop tool-use demo](tool_demo.mov)

---

## Architecture

```text
            Greenhouse / Lever / Ashby
                       |
                       v
                     Scout
             Public job-board APIs
                       |
                       v
                    Extractor
              Qwen 2.5 7B via Ollama
                       |
                 failure / fallback
                       |
                       v
                Claude Haiku 4.5
                       |
                       v
               Structured ExtractedJob
                       |
                       v
                     Matcher
        sentence-transformers + cosine similarity
                       |
                       v
              Ranked resume bullets
                       |
                       v
                     SQLite
                   /        \
                  v          v
        Streamlit Dashboard  MCP Server
                                  |
                                  v
                         Claude Desktop / MCP Client
```

The Scout currently supports public **Greenhouse, Lever, and Ashby** job-board APIs. Each ATS response is normalized before entering the rest of the pipeline, allowing the extractor and matcher to operate independently of the original job-board format.

The Extractor attempts local inference with Qwen first and automatically falls back to Claude if the local model fails or produces invalid structured output. The Matcher maps each extracted role to the appropriate resume track and uses MiniLM sentence embeddings and cosine similarity to rank the strongest supporting resume bullets.

---

## Open vs. Closed Model Evaluation

Both models were evaluated against the same hand-labeled benchmark of 10 real job postings.

| Model            | Exact Field Accuracy | Required Skill F1 | Preferred Skill F1 | Schema Validity | Avg Latency | Input Tokens | Output Tokens |        Est. Cost |
| ---------------- | -------------------: | ----------------: | -----------------: | --------------: | ----------: | -----------: | ------------: | ---------------: |
| Claude Haiku 4.5 |                68.0% |             0.000 |              0.100 |           10/10 |       5.21s |       29,624 |         1,567 |          $0.0375 |
| Qwen 2.5 7B      |            **78.0%** |         **0.456** |          **0.466** |           10/10 |       7.21s |       20,822 |         1,476 | $0.0000 API cost |

The benchmark measures:

* **Exact Field Accuracy** — correctness of structured fields such as role type, organization, location, minimum experience, and internship status.
* **Skill F1** — balances precision and recall when comparing extracted required/preferred skills against hand-labeled skill sets.
* **Schema Validity** — whether the model produced output that successfully validated against the Pydantic extraction schema.
* **Latency, token usage, and cost** — operational tradeoffs relevant to running the pipeline at larger scale.

The results motivated the current **Ollama-first, Claude-fallback** design: local Qwen inference avoids API cost while Claude remains available as a reliability fallback.

---

## MCP Integration

The application's core capabilities are also exposed as MCP tools:

* `fetch_postings` — retrieve and filter live job postings
* `extract_job_fields` — convert raw posting text into a structured job representation
* `match_to_resume` — rank the most relevant resume bullets for an extracted role

This allows an external MCP client such as Claude Desktop to decide when to invoke each capability.

In the recorded demo, Claude autonomously:

```text
fetches postings
      ↓
extracts job requirements
      ↓
matches the role against the appropriate resume track
      ↓
returns the strongest supporting bullets
```

This provides a second interface to the same underlying system beyond the predetermined LangGraph batch workflow.

---

## Dashboard

The deployed Streamlit dashboard reads precomputed pipeline results from SQLite and allows users to:

* browse processed internship postings
* filter by role type
* inspect structured job requirements
* see which model performed the extraction
* view required and preferred skills
* review the highest-ranked resume bullets and their similarity scores

**Live:** https://application-copilot.streamlit.app/

---

## What I Would Build Next

### Autonomous Job Monitoring

Turn the current on-demand workflow into a continuously running recruiting assistant.

Instead of requiring a board token or manual pipeline execution, the system would periodically monitor a configured list of target companies across Greenhouse, Lever, and Ashby, identify newly posted internships, deduplicate postings already seen, extract their requirements, and automatically score them against the appropriate resume track.

For sufficiently strong matches, the system could send an **email notification containing the role, match information, and a direct application link**.

```text
Scheduled Scout
      ↓
Detect new posting
      ↓
Extract requirements
      ↓
Match against resume
      ↓
High-confidence match?
      |
      +── No → store silently
      |
      +── Yes
             ↓
       Email notification
             ↓
      Job + company + match
      score + application link
```

### Direct Application Links

Extend the normalized posting schema to preserve each ATS's application URL (`hostedUrl`, `jobUrl`, or equivalent). The dashboard and MCP responses could then surface an **Apply** link alongside every matched posting, turning the project from an evaluation dashboard into a more useful recruiting workflow.

A later version could combine these features into a personalized feed of newly discovered roles ranked by fit rather than requiring the user to manually search individual company job boards.
