from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean
from typing import Any, Callable

from src.extractor.extract import extract_with_claude, extract_with_ollama


BENCHMARK_PATH = Path("data/extractor_benchmark.json")
RESULTS_PATH = Path("data/extractor_benchmark_results.json")

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
OLLAMA_MODEL = "qwen2.5:7b"

# Standard Claude Haiku 4.5 API pricing (USD / 1M tokens).
CLAUDE_INPUT_PER_MILLION = 1.00
CLAUDE_OUTPUT_PER_MILLION = 5.00

SCALAR_FIELDS = [
    "organization",
    "role_type",
    "min_years_experience",
    "location",
    "is_internship",
]


def normalize_text(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^\w\s/+&.-]", "", value)
    return re.sub(r"\s+", " ", value)


def normalize_scalar(value: Any) -> Any:
    if isinstance(value, str):
        return normalize_text(value)
    return value


def scalar_accuracy(job: Any, expected: dict) -> float:
    hits = 0
    for field in SCALAR_FIELDS:
        predicted = normalize_scalar(getattr(job, field))
        truth = normalize_scalar(expected[field])
        hits += int(predicted == truth)
    return hits / len(SCALAR_FIELDS)


def skill_f1(predicted: list[str], expected: list[str]) -> float:
    pred = {normalize_text(x) for x in predicted}
    gold = {normalize_text(x) for x in expected}

    if not pred and not gold:
        return 1.0
    if not pred or not gold:
        return 0.0

    overlap = len(pred & gold)
    precision = overlap / len(pred)
    recall = overlap / len(gold)

    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def run_model(
    name: str,
    extractor: Callable,
    model: str,
    cases: list[dict],
) -> tuple[dict, list[dict]]:
    scalar_scores: list[float] = []
    required_f1s: list[float] = []
    preferred_f1s: list[float] = []
    latencies: list[float] = []
    input_tokens = 0
    output_tokens = 0
    valid_outputs = 0
    detailed: list[dict] = []

    for index, case in enumerate(cases, start=1):
        print(
            f"{name} [{index}/{len(cases)}]: "
            f"{case['company']} — {case['title']}"
        )

        try:
            result = extractor(
                case["raw_text"],
                company=case["company"],
                title=case["title"],
                model=model,
            )

            job = result.job
            scalar = scalar_accuracy(job, case["expected"])
            req_f1 = skill_f1(
                job.required_skills,
                case["expected"]["required_skills"],
            )
            pref_f1 = skill_f1(
                job.preferred_skills,
                case["expected"]["preferred_skills"],
            )

            scalar_scores.append(scalar)
            required_f1s.append(req_f1)
            preferred_f1s.append(pref_f1)
            latencies.append(result.latency_seconds)
            input_tokens += result.input_tokens or 0
            output_tokens += result.output_tokens or 0
            valid_outputs += 1

            detailed.append({
                "id": case["id"],
                "status": "ok",
                "prediction": job.model_dump(),
                "expected": case["expected"],
                "scalar_accuracy": scalar,
                "required_skill_f1": req_f1,
                "preferred_skill_f1": pref_f1,
                "latency_seconds": result.latency_seconds,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
            })

        except Exception as exc:
            # A first-pass validation/schema failure is itself a benchmark result.
            scalar_scores.append(0.0)
            required_f1s.append(0.0)
            preferred_f1s.append(0.0)

            detailed.append({
                "id": case["id"],
                "status": "error",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "expected": case["expected"],
            })

            print(f"  ERROR: {type(exc).__name__}: {exc}")

    metrics = {
        "model": model,
        "scalar_accuracy": mean(scalar_scores),
        "required_skill_f1": mean(required_f1s),
        "preferred_skill_f1": mean(preferred_f1s),
        "valid_outputs": valid_outputs,
        "total_cases": len(cases),
        "average_latency_seconds": mean(latencies) if latencies else None,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    return metrics, detailed


def main() -> None:
    with BENCHMARK_PATH.open(encoding="utf-8") as f:
        cases = json.load(f)

    claude, claude_details = run_model(
        "Claude",
        extract_with_claude,
        CLAUDE_MODEL,
        cases,
    )
    qwen, qwen_details = run_model(
        "Qwen",
        extract_with_ollama,
        OLLAMA_MODEL,
        cases,
    )

    claude_cost = (
        claude["input_tokens"] / 1_000_000 * CLAUDE_INPUT_PER_MILLION
        + claude["output_tokens"] / 1_000_000 * CLAUDE_OUTPUT_PER_MILLION
    )
    claude["estimated_cost_usd"] = claude_cost
    qwen["estimated_cost_usd"] = 0.0

    results = {
        "metrics": {
            "claude": claude,
            "qwen": qwen,
        },
        "cases": {
            "claude": claude_details,
            "qwen": qwen_details,
        },
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    def latency(metric: dict) -> str:
        value = metric["average_latency_seconds"]
        return "N/A" if value is None else f"{value:.2f}s"

    print("\nREADME-ready comparison table:\n")
    print(
        "| Model | Scalar Accuracy | Required Skill F1 | Preferred Skill F1 "
        "| Valid Outputs | Avg Latency | Input Tokens | Output Tokens | Est. Cost |"
    )
    print(
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    )
    print(
        f"| Claude Haiku 4.5 | {claude['scalar_accuracy']:.1%} | "
        f"{claude['required_skill_f1']:.3f} | "
        f"{claude['preferred_skill_f1']:.3f} | "
        f"{claude['valid_outputs']}/{claude['total_cases']} | "
        f"{latency(claude)} | {claude['input_tokens']} | "
        f"{claude['output_tokens']} | ${claude_cost:.4f} |"
    )
    print(
        f"| Qwen 2.5 7B | {qwen['scalar_accuracy']:.1%} | "
        f"{qwen['required_skill_f1']:.3f} | "
        f"{qwen['preferred_skill_f1']:.3f} | "
        f"{qwen['valid_outputs']}/{qwen['total_cases']} | "
        f"{latency(qwen)} | {qwen['input_tokens']} | "
        f"{qwen['output_tokens']} | $0.0000 |"
    )

    print(f"\nDetailed results saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
    