"""Isolation test for the TypeSafe question specs (plan step 4), run against
real seeded data before wiring into the /recommendations endpoint.
"""

from sqlmodel import Session, select

from app.db import engine
from app.judgments.typesafe_client import (
    candidate_state,
    hard_filter_question,
    run_judgments,
    taste_fit_question,
    tie_break_question,
    user_state,
)
from app.models import Item, ItemType, PreferenceNote, Rating, User


def load_user_context(session: Session, user_id: int) -> tuple[str, list[str], list[str]]:
    note = session.exec(
        select(PreferenceNote).where(PreferenceNote.user_id == user_id)
    ).first()
    ratings = session.exec(select(Rating).where(Rating.user_id == user_id)).all()

    liked, disliked = [], []
    for r in ratings:
        item = session.get(Item, r.item_id)
        if not item:
            continue
        (liked if r.value > 0 else disliked).append(item.title)

    return (note.text if note else "", liked, disliked)


def test_score_and_filter(session: Session, user: User, candidate: Item) -> None:
    taste_note, liked, disliked = load_user_context(session, user.id)
    state = {
        "user": user_state(taste_note, liked, disliked),
        "candidate": candidate_state(candidate.model_dump()),
    }

    response = run_judgments(
        state,
        {
            "fit": taste_fit_question("user", "candidate"),
            "conflict": hard_filter_question("user", "candidate"),
        },
    )
    print(f"\n[score/noul] candidate={candidate.title!r} user={user.name!r}")
    print(f"  model={response.model} usage={response.usage}")
    print(f"  fit={response.answers['fit']}")
    print(f"  conflict={response.answers['conflict']}")


def test_tie_break(candidates: list[Item]) -> None:
    labels = [c.title for c in candidates]
    state = {
        "context": {"mood": "relaxed weeknight, nothing too heavy"},
        "options": [{"title": c.title, "metadata": c.item_metadata} for c in candidates],
    }
    response = run_judgments(state, {"pick": tie_break_question(labels)})
    print(f"\n[choice] tie-break among {labels}")
    print(f"  model={response.model} usage={response.usage}")
    print(f"  pick={response.answers['pick']}")


def main() -> None:
    with Session(engine) as session:
        user = session.exec(select(User)).first()
        assert user, "seed users first: python scripts/seed_users.py"

        candidates = session.exec(
            select(Item).where(Item.type == ItemType.movie).limit(2)
        ).all()
        assert len(candidates) >= 2, "sync items first: python scripts/sync_items.py"

        test_score_and_filter(session, user, candidates[0])
        test_tie_break(candidates)


if __name__ == "__main__":
    main()
