"""TypeSafe (Jev) question specs: the showcased judgment layer.

Ranking/filtering/tie-breaking logic runs through typed Score/Noul/Choice
questions here, not free-text LLM prompts. Composite scoring across the two
users still happens in plain code (see app/recommend/), not in a model call.
"""

from typing import Any

from typesafe_sdk import Choice, Noul, Score, SystemOneResponse, TypeSafeClient

from app.config import settings

TASTE_SCORE_LEVELS = [
    "no interest",
    "mild interest",
    "interested",
    "excited",
    "must do",
]


def get_client() -> TypeSafeClient:
    return TypeSafeClient(api_key=settings.typesafe_api_key)


def taste_fit_question() -> Score:
    """Per-user taste fit for one candidate, given `candidate` in state."""
    return Score(
        instructions=(
            "Given this person's `taste_note` and their `liked_titles`/"
            "`disliked_titles` history, how excited would they be to watch or "
            "visit `candidate`?"
        ),
        criteria=TASTE_SCORE_LEVELS,
    )


def hard_filter_question() -> Noul:
    """Whether `candidate` conflicts with something the person explicitly ruled out."""
    return Noul(
        instructions=(
            "Does `candidate` conflict with anything this person explicitly said "
            "they dislike, are allergic to, or want to avoid, per their "
            "`taste_note` or `disliked_titles`?"
        ),
        criteria={
            "true": "conflicts with a stated dislike or restriction",
            "false": "no conflict",
        },
    )


def tie_break_question(candidate_labels: list[str]) -> Choice:
    """Situational tie-break across a shortlist, given `context` in state."""
    return Choice(
        instructions=(
            "Given tonight's `context` (mood/occasion), which of these "
            "candidates best fits right now?"
        ),
        criteria={label: None for label in candidate_labels},
    )


def build_taste_state(
    taste_note: str,
    liked_titles: list[str],
    disliked_titles: list[str],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "taste_note": taste_note or "(no note provided)",
        "liked_titles": liked_titles,
        "disliked_titles": disliked_titles,
        "candidate": {
            "title": candidate["title"],
            "type": candidate["type"],
            "metadata": candidate.get("item_metadata", {}),
        },
    }


def run_judgments(state: dict[str, Any], questions: dict[str, Any]) -> SystemOneResponse:
    with get_client() as client:
        return client.system_one(state=state, questions=questions)
