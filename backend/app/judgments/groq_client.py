"""Groq-hosted open-source model: non-judgment free-text generation only.

Anything that's a typed decision (ranking/filtering/tie-breaking) belongs in
typesafe_client.py instead. This module only ever produces free text or
lightly-structured extraction from free text.
"""

import json
from typing import Any

from groq import Groq

from app.config import settings

MODEL = "openai/gpt-oss-20b"


def get_client() -> Groq:
    return Groq(api_key=settings.groq_api_key)


def generate_blurb(
    item_title: str,
    item_type: str,
    score_summary: dict[str, Any],
) -> str:
    """Short "why this" blurb for the top pick, grounded in the actual scores
    (not asked to invent its own judgment)."""
    prompt = (
        f"In one upbeat sentence (max 25 words), explain why \"{item_title}\" "
        f"(a {item_type}) is tonight's pick for a couple, given these per-person "
        f"taste-fit scores: {json.dumps(score_summary)}. "
        "Do not invent details not implied by the scores. No preamble."
    )
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.7,
        extra_body={"reasoning_effort": "low"},
    )
    return response.choices[0].message.content.strip()


def parse_preference_note(text: str) -> dict[str, list[str]]:
    """Parse a freeform taste note into structured tags for downstream use
    (e.g. to seed liked/disliked genre lists). Extraction, not judgment."""
    prompt = (
        "Extract structured tags from this person's freeform taste note. "
        'Respond with strict JSON: {"likes": [...], "dislikes": [...], '
        '"restrictions": [...]}. Use short lowercase phrases. If a category '
        "has nothing, use an empty list.\n\n"
        f"Note: {text}"
    )
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0,
        extra_body={"reasoning_effort": "low"},
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
