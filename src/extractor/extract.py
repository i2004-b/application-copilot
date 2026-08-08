"""
Extractor agent: turns raw job-posting text into an ExtractedJob.

Two implementations on purpose -- this is the "open-source vs. closed-source
model" comparison from the project plan:

  extract_with_claude()  -- closed-source, forces structured output via
                             Anthropic tool use. Higher accuracy, costs
                             real tokens.
  extract_with_ollama()  -- open-source model running locally via Ollama.
                             Free and private, but you should expect to
                             measure a real accuracy gap -- that gap (and
                             what it costs to close) IS the deliverable.

Week 1 task:
  1. Get extract_with_claude() working on ~10 real postings.
  2. Get extract_with_ollama() working on the same 10.
  3. Hand-label the "correct" answers for those 10 and write a tiny script
     (see scripts/compare_models.py once you build it) that reports
     accuracy, latency, and $ cost per model. That table goes straight into
     your README.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

import requests
from anthropic import Anthropic

from src.config import settings
from src.extractor.schemas import ExtractedJob

_client = Anthropic(api_key=settings.anthropic_api_key) # Creates re-usable connection instance to Anthropic

# Dictionary --> tool specification for claude
_EXTRACTION_TOOL = {
    # Name is the function idenfier Claude will invoke
    "name": "record_extracted_job", # No function for this; giving LLM a form a saying to fill it out
    "description": "Record structured fields extracted from a job posting.", # Telling what the tool is for
    # Takes pydantic blueprint and translates into standard JSON schema format so claude understands exact fields
    "input_schema": ExtractedJob.model_json_schema(),
}


@dataclass
# Like a lightweight custom data object and gives experiment metadata
class ExtractionResult:
    job: ExtractedJob
    model: str
    latency_seconds: float
    input_tokens: int | None = None
    output_tokens: int | None = None

"""
Takes raw job description
"""
def extract_with_claude(raw_jd_text: str, model: str | None = None) -> ExtractionResult:
    """Force Claude to call record_extracted_job with structured fields."""
    model = model or settings.closed_model
    start = time.perf_counter()
    response = _client.messages.create(
        model=model,
        max_tokens=1024,
        tools=[_EXTRACTION_TOOL], # LLM API tool declaration
        tool_choice={"type": "tool", "name": "record_extracted_job"}, # Forces claude to bypass normal text generation entirely 
        messages=[
            {
                "role": "user",
                "content": f"Extract structured fields from this job posting:\n\n{raw_jd_text}",
            }
        ],
    )
    latency = time.perf_counter() - start

    for block in response.content: # response.content comes back as list of blocks
        if block.type == "tool_use" and block.name == "record_extracted_job": # Checks if claude actually respond using the tool
            job = ExtractedJob(**block.input) # ** --> unpacking into ExtractedJob pydantic class to validate that the types are correct
            return ExtractionResult(
                job=job,
                model=model,
                latency_seconds=latency,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
    raise ValueError("Claude did not return a tool_use block -- inspect response.content")


def extract_with_ollama(raw_jd_text: str, model: str | None = None) -> ExtractionResult:
    """
    Same task, run against a local Ollama model. Requires `ollama serve`
    running and the model already pulled (`ollama pull <model>`).

    Ollama's /api/chat supports `"format": "json"` to bias toward valid
    JSON, but -- unlike Claude's forced tool use -- it isn't guaranteed to
    match your schema. Expect to add retry/repair logic here; that's part
    of the point of the comparison.
    """
    model = model or settings.ollama_model
    schema = ExtractedJob.model_json_schema()
    prompt = (
        "Extract structured fields from this job posting. "
        f"Respond with ONLY valid JSON matching this schema:\n{json.dumps(schema)}\n\n"
        f"Job posting:\n{raw_jd_text}"
    )

    start = time.perf_counter()
    resp = requests.post(
        f"{settings.ollama_host}/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "format": "json",
            "stream": False,
        },
        timeout=60,
    )
    resp.raise_for_status()
    latency = time.perf_counter() - start

    payload = resp.json()
    content = payload["message"]["content"]
    job = ExtractedJob(**json.loads(content))
    return ExtractionResult(
        job=job,
        model=model,
        latency_seconds=latency,
        input_tokens=payload.get("prompt_eval_count"),
        output_tokens=payload.get("eval_count"),
    )


# Testing script
if __name__ == "__main__":
    # Import from the scout folder whichever platform you want to test: greenhouse, ashby, lever
    from src.scout.greenhouse import fetch_postings

    # Save the posting for the company
    postings = fetch_postings("stripe")

    # Execute if the postings exist
    if postings:
        # Get a sample
        sample = postings[0]

        # Get content in the posting
        raw_text = sample.get("content", "")

        # Extract the fields
        print(f"Extracting fields for: {sample.get("title")}...")

        # Call extract with claude

        print(sample)

        print("\n--- RAW TEXT SENT TO MODELS ---")
        print(raw_text[:3000])

        # result_closed = extract_with_claude(raw_text, "claude-haiku-4-5-20251001")
        # result_open = extract_with_ollama(raw_text, "qwen2.5:7b")

        # # Print the results from closed model --> Claude Haiku 4.5
        # print("\n--- Extracted Result (Closed Model) ---")
        # print(f"Company: {result_closed.job.company}")
        # print(f"Title: {result_closed.job.title}")
        # print(f"Role Type: {result_closed.job.role_type}")
        # print(f"Skills: {result_closed.job.required_skills}")
        # print(f"Min Years: {result_closed.job.min_years_experience}")
        # print(f"Location: {result_closed.job.location}")
        # print(f"Is Internship: {result_closed.job.is_internship}")
        # print(f"Summary: {result_closed.job.summary}")
        # print(f"\nLatency: {result_closed.latency_seconds:.2f}s | Tokens (In/Out): {result_closed.input_tokens}/{result_closed.output_tokens}")

        # # Print the results --> Qwen
        # print("\n--- Extracted Result (Open Model) ---")
        # print(f"Company: {result_open.job.company}")
        # print(f"Title: {result_open.job.title}")
        # print(f"Role Type: {result_open.job.role_type}")
        # print(f"Skills: {result_open.job.required_skills}")
        # print(f"Min Years: {result_open.job.min_years_experience}")
        # print(f"Location: {result_open.job.location}")
        # print(f"Is Internship: {result_open.job.is_internship}")
        # print(f"Summary: {result_open.job.summary}")
        # print(f"\nLatency: {result_open.latency_seconds:.2f}s | Tokens (In/Out): {result_open.input_tokens}/{result_open.output_tokens}")


