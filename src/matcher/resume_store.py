"""
Matcher agent, part 1: embeds your resume bullets once and holds them in
memory so any extracted job can be scored against them via cosine similarity.

data/resume_bullets.example.json has 6 generic placeholder bullets so this
runs out of the box. Week 2 task: replace it with your own real bullets
(one JSON object per bullet -- see the format below) across all three of
your resume tracks (SWE/AI Engineer, AI/ML Researcher, TPM/PM), so the
matcher can recommend the right *version* of a bullet depending on which
track a posting is tagged as.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, good enough for this


class ResumeStore:
    def __init__(self, bullets_path: str = "data/resume_bullets.example.json"):
        self.bullets: list[dict] = json.loads(Path(bullets_path).read_text())
        self.model = SentenceTransformer(_MODEL_NAME)
        self.embeddings = self.model.encode(
            [b["text"] for b in self.bullets], normalize_embeddings=True
        )

    def top_matches(self, query: str, k: int = 5, track: str | None = None) -> list[dict]:
        """
        Return the k resume bullets most similar to `query` (typically the
        extracted job's summary + required_skills joined into one string).

        If `track` is given (e.g. "AI/ML Engineer"), only bullets tagged
        with that track are considered -- this is what lets the same
        posting pull different bullets depending on which resume version
        you're tailoring.
        """
        candidates = self.bullets
        candidate_embeddings = self.embeddings
        if track is not None:
            mask = [i for i, b in enumerate(self.bullets) if track in b.get("tracks", [])]
            candidates = [self.bullets[i] for i in mask]
            candidate_embeddings = self.embeddings[mask]
            if not candidates:
                return []

        q_emb = self.model.encode([query], normalize_embeddings=True)[0]
        scores = candidate_embeddings @ q_emb
        top_idx = np.argsort(-scores)[:k]
        return [{**candidates[i], "score": float(scores[i])} for i in top_idx]
