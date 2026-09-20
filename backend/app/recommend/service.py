from sqlmodel import Session, select

from app.judgments.groq_client import generate_blurb
from app.judgments.typesafe_client import (
    candidate_state,
    hard_filter_question,
    run_judgments,
    taste_fit_question,
    tie_break_question,
    user_state,
)
from app.models import Item, PreferenceNote, Rating, RecommendationLog, User
from app.recommend.schemas import (
    RankedCandidate,
    RankingMode,
    RecommendationRequest,
    RecommendationResponse,
    TopPick,
)


def _load_user_context(session: Session, user_id: int) -> tuple[str, list[str], list[str]]:
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


def _fetch_unrated_candidates(session: Session, item_type, limit: int) -> list[Item]:
    rated_item_ids = set(session.exec(select(Rating.item_id)).all())
    candidates = session.exec(select(Item).where(Item.type == item_type)).all()
    unrated = [c for c in candidates if c.id not in rated_item_ids]
    return unrated[:limit]


def _composite(scores: list[float], mode: RankingMode) -> float:
    if mode == RankingMode.both_must_like:
        return min(scores)
    return sum(scores) / len(scores)


def build_recommendations(
    session: Session, request: RecommendationRequest
) -> RecommendationResponse:
    users = session.exec(select(User)).all()
    if len(users) < 2:
        raise ValueError("expected at least 2 seeded users")

    candidates = _fetch_unrated_candidates(
        session, request.item_type, request.candidate_pool_size
    )
    if not candidates:
        raise ValueError("no unrated candidates available for this type")

    user_contexts = {u.id: _load_user_context(session, u.id) for u in users}

    state: dict = {
        "users": [
            user_state(*user_contexts[u.id]) for u in users
        ],
        "candidates": [candidate_state(c.model_dump()) for c in candidates],
    }

    questions = {}
    for u_idx in range(len(users)):
        for c_idx in range(len(candidates)):
            user_path = f"users[{u_idx}]"
            candidate_path = f"candidates[{c_idx}]"
            questions[f"score_{u_idx}_{c_idx}"] = taste_fit_question(user_path, candidate_path)
            questions[f"filter_{u_idx}_{c_idx}"] = hard_filter_question(user_path, candidate_path)

    response = run_judgments(state, questions)

    per_user_scores: dict[int, dict[int, float]] = {u.id: {} for u in users}
    filtered_out: set[int] = set()

    for u_idx, user in enumerate(users):
        for c_idx, candidate in enumerate(candidates):
            score_answer = response.answers[f"score_{u_idx}_{c_idx}"]
            filter_answer = response.answers[f"filter_{u_idx}_{c_idx}"]
            per_user_scores[user.id][candidate.id] = score_answer.score
            if filter_answer.noul > 0.5:
                filtered_out.add(candidate.id)

    surviving = [c for c in candidates if c.id not in filtered_out]
    if not surviving:
        surviving = candidates  # don't zero out the whole pool on an overzealous filter

    ranked_candidates = []
    for c in surviving:
        scores = [per_user_scores[u.id][c.id] for u in users]
        composite = _composite(scores, request.mode)
        ranked_candidates.append((c, composite))

    ranked_candidates.sort(key=lambda pair: pair[1], reverse=True)
    top = ranked_candidates[: request.top_n]

    ranked = [
        RankedCandidate(
            item_id=c.id,
            title=c.title,
            per_user_scores={u.id: per_user_scores[u.id][c.id] for u in users},
            composite_score=composite,
        )
        for c, composite in top
    ]

    top_pick_item = None
    if len(top) == 1:
        top_pick_item = top[0][0]
    elif len(top) > 1:
        shortlist = top[: request.shortlist_n]
        labels = [f"{c.title} ({c.id})" for c, _ in shortlist]
        tie_break_state = {
            "context": request.context or {"mood": "no particular mood specified"},
            "options": [candidate_state(c.model_dump()) for c, _ in shortlist],
        }
        tie_response = run_judgments(
            tie_break_state, {"pick": tie_break_question(labels)}
        )
        chosen_label = tie_response.answers["pick"].choice
        chosen_id = int(chosen_label.rsplit("(", 1)[1].rstrip(")"))
        top_pick_item = next(c for c, _ in shortlist if c.id == chosen_id)

    top_pick = None
    if top_pick_item:
        pick_scores = {u.id: per_user_scores[u.id][top_pick_item.id] for u in users}
        blurb = generate_blurb(
            top_pick_item.title,
            top_pick_item.type.value,
            {str(u.id): score for u, score in zip(users, pick_scores.values())},
        )
        top_pick = TopPick(
            item_id=top_pick_item.id,
            title=top_pick_item.title,
            per_user_scores=pick_scores,
            blurb=blurb,
        )

    log = RecommendationLog(
        context=request.context,
        results={
            "item_type": request.item_type.value,
            "mode": request.mode.value,
            "ranked": [r.model_dump() for r in ranked],
            "top_pick": top_pick.model_dump() if top_pick else None,
        },
    )
    session.add(log)
    session.commit()
    session.refresh(log)

    return RecommendationResponse(ranked=ranked, top_pick=top_pick, log_id=log.id)
