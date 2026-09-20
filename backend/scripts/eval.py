"""Hand-labeled eval for the TypeSafe judgment layer.

Runs a fixed set of taste-fit (Score) and conflict (Noul) scenarios against
the live API in one batched call, then checks each answer against an
expected outcome. This is what makes "the AI depth is real" more than a
demo that happened to work once - re-run after any prompt/spec change to
catch regressions.

Scenarios use synthetic user/candidate data (not the live DB) so the eval
set is stable and independent of what TMDB/Google Places happen to return
on a given day.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from app.judgments.typesafe_client import (
    candidate_state,
    hard_filter_question,
    run_judgments,
    taste_fit_question,
    user_state,
)

Kind = Literal["score_min", "score_max", "noul"]


@dataclass
class Scenario:
    name: str
    kind: Kind
    user: dict[str, Any]
    candidate: dict[str, Any]
    expect: Any  # float threshold for score_min/score_max, bool for noul


SCENARIOS: list[Scenario] = [
    # -- Score: should rate HIGH (taste matches candidate) --
    Scenario(
        "loves_thrillers_gets_thriller",
        "score_min",
        user_state("I love slow-burn psychological thrillers.", [], []),
        candidate_state({"title": "The Quiet Room", "type": "movie",
                          "item_metadata": {"overview": "A slow-burn psychological thriller about a woman unraveling a conspiracy.", "genre_ids": [53]}}),
        2.0,
    ),
    Scenario(
        "loves_italian_gets_italian_restaurant",
        "score_min",
        user_state("Big fan of Italian food, especially fresh pasta.", [], []),
        candidate_state({"title": "Nonna's Table", "type": "restaurant",
                          "item_metadata": {"primary_type": "italian_restaurant", "cuisine_types": ["italian_restaurant"]}}),
        2.0,
    ),
    Scenario(
        "liked_similar_show_gets_similar_show",
        "score_min",
        user_state("", ["Breaking Bad", "Better Call Saul"], []),
        candidate_state({"title": "Ozark", "type": "tv",
                          "item_metadata": {"overview": "A financial planner launders money for a drug cartel after a scheme goes wrong.", "genre_ids": [80, 18]}}),
        2.0,
    ),
    Scenario(
        "loves_comedy_gets_comedy",
        "score_min",
        user_state("I mostly want light, funny stuff after work.", [], []),
        candidate_state({"title": "Office Antics", "type": "movie",
                          "item_metadata": {"overview": "A workplace comedy about a chaotic startup office.", "genre_ids": [35]}}),
        2.0,
    ),
    Scenario(
        "vegetarian_gets_vegetarian_restaurant",
        "score_min",
        user_state("Vegetarian, love Thai and Indian food.", [], []),
        candidate_state({"title": "Green Leaf Thai", "type": "restaurant",
                          "item_metadata": {"primary_type": "thai_restaurant", "cuisine_types": ["thai_restaurant", "vegetarian_restaurant"]}}),
        2.0,
    ),
    # -- Score: should rate LOW (taste conflicts, but not a hard "restriction" -> tests Score, not Noul) --
    Scenario(
        "hates_horror_gets_horror",
        "score_max",
        user_state("I really dislike horror movies, they stress me out.", [], []),
        candidate_state({"title": "Night Terror", "type": "movie",
                          "item_metadata": {"overview": "A masked killer stalks a family through a haunted house.", "genre_ids": [27]}}),
        2.0,
    ),
    Scenario(
        "disliked_show_gets_similar_show",
        "score_max",
        user_state("", [], ["The Bachelor", "Love Island"]),
        candidate_state({"title": "Dating Around", "type": "tv",
                          "item_metadata": {"overview": "Singles go on blind dates hoping to find love.", "genre_ids": [10764]}}),
        2.0,
    ),
    Scenario(
        "hates_spicy_gets_spicy_cuisine",
        "score_max",
        user_state("Can't handle spicy food at all.", [], []),
        candidate_state({"title": "Sichuan Fire House", "type": "restaurant",
                          "item_metadata": {"primary_type": "sichuan_restaurant", "cuisine_types": ["sichuan_restaurant"]}}),
        2.0,
    ),
    Scenario(
        "wants_light_gets_heavy_drama",
        "score_max",
        user_state("I only want light, easy-watching stuff this week, nothing heavy.", [], []),
        candidate_state({"title": "The Long Grief", "type": "movie",
                          "item_metadata": {"overview": "A devastating multi-generational drama about loss and war.", "genre_ids": [18]}}),
        2.0,
    ),
    # -- Noul: SHOULD flag a conflict (explicit restriction/dislike) --
    Scenario(
        "shellfish_allergy_flags_seafood",
        "noul",
        user_state("Allergic to shellfish, please avoid seafood-heavy spots.", [], []),
        candidate_state({"title": "The Lobster Shack", "type": "restaurant",
                          "item_metadata": {"primary_type": "seafood_restaurant", "cuisine_types": ["seafood_restaurant"]}}),
        True,
    ),
    Scenario(
        "hates_jump_scares_flags_horror",
        "noul",
        user_state("I hate jump scares, please never recommend horror.", [], []),
        candidate_state({"title": "The Basement", "type": "movie",
                          "item_metadata": {"overview": "A found-footage horror film full of jump scares.", "genre_ids": [27]}}),
        True,
    ),
    Scenario(
        "explicit_dislike_title_genre_flags_sequel",
        "noul",
        user_state("", [], ["Saw", "Saw II"]),
        candidate_state({"title": "Saw III", "type": "movie",
                          "item_metadata": {"overview": "The Jigsaw killer's traps continue in this gory horror sequel.", "genre_ids": [27]}}),
        True,
    ),
    Scenario(
        "gluten_free_flags_pasta_place",
        "noul",
        user_state("Celiac - strictly gluten-free, cannot eat wheat/pasta/bread.", [], []),
        candidate_state({"title": "Pasta Palace", "type": "restaurant",
                          "item_metadata": {"primary_type": "italian_restaurant", "cuisine_types": ["italian_restaurant"]}}),
        True,
    ),
    # -- Noul: should NOT flag a conflict (no stated restriction) --
    Scenario(
        "no_restrictions_no_conflict_restaurant",
        "noul",
        user_state("Open to anything, love trying new cuisines.", [], []),
        candidate_state({"title": "Fusion Kitchen", "type": "restaurant",
                          "item_metadata": {"primary_type": "restaurant", "cuisine_types": ["fusion_restaurant"]}}),
        False,
    ),
    Scenario(
        "unrelated_dislike_no_conflict",
        "noul",
        user_state("I dislike slow arthouse films.", [], []),
        candidate_state({"title": "Galaxy Raiders", "type": "movie",
                          "item_metadata": {"overview": "A fast-paced space action blockbuster.", "genre_ids": [878, 28]}}),
        False,
    ),
    Scenario(
        "mild_preference_no_conflict",
        "noul",
        user_state("I'd slightly prefer something upbeat tonight.", [], []),
        candidate_state({"title": "Quiet Streets", "type": "tv",
                          "item_metadata": {"overview": "A slow character-driven drama set in a small town.", "genre_ids": [18]}}),
        False,
    ),
]


def _build_state_and_questions() -> tuple[dict[str, Any], dict[str, Any]]:
    state: dict[str, Any] = {"scenarios": []}
    questions: dict[str, Any] = {}

    for idx, scenario in enumerate(SCENARIOS):
        state["scenarios"].append({"user": scenario.user, "candidate": scenario.candidate})
        user_path = f"scenarios[{idx}].user"
        candidate_path = f"scenarios[{idx}].candidate"
        if scenario.kind in ("score_min", "score_max"):
            questions[f"q_{idx}"] = taste_fit_question(user_path, candidate_path)
        else:
            questions[f"q_{idx}"] = hard_filter_question(user_path, candidate_path)

    return state, questions


def run_eval() -> dict[str, Any]:
    state, questions = _build_state_and_questions()
    response = run_judgments(state, questions)

    results = []
    for idx, scenario in enumerate(SCENARIOS):
        answer = response.answers[f"q_{idx}"]
        if scenario.kind == "score_min":
            actual = answer.score
            passed = actual >= scenario.expect
        elif scenario.kind == "score_max":
            actual = answer.score
            passed = actual <= scenario.expect
        else:  # noul
            actual = answer.noul > 0.5
            passed = actual == scenario.expect

        results.append(
            {
                "name": scenario.name,
                "kind": scenario.kind,
                "expected": scenario.expect,
                "actual": actual,
                "passed": passed,
            }
        )

    noul_results = [r for r in results if r["kind"] == "noul"]
    tp = sum(1 for r in noul_results if r["expected"] and r["actual"])
    fp = sum(1 for r in noul_results if not r["expected"] and r["actual"])
    fn = sum(1 for r in noul_results if r["expected"] and not r["actual"])
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None

    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "accuracy": sum(1 for r in results if r["passed"]) / len(results),
        "noul_precision": precision,
        "noul_recall": recall,
        "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
    }

    return {"results": results, "summary": summary}


def main() -> None:
    report = run_eval()

    for r in report["results"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"[{status}] {r['name']} ({r['kind']}) expected={r['expected']} actual={r['actual']}")

    s = report["summary"]
    print("\n--- summary ---")
    print(f"accuracy: {s['passed']}/{s['total']} ({s['accuracy']:.0%})")
    if s["noul_precision"] is not None:
        print(f"noul precision: {s['noul_precision']:.2f}, recall: {s['noul_recall']:.2f}")
    print(f"usage: {s['usage']}")

    out_path = Path(__file__).parent / "eval_results.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
