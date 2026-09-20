from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.models.tables import ItemType


class RankingMode(str, Enum):
    both_must_like = "both_must_like"
    weighted = "weighted"


class RecommendationRequest(BaseModel):
    item_type: ItemType
    mode: RankingMode = RankingMode.both_must_like
    context: dict[str, Any] = {}
    candidate_pool_size: int = 12
    top_n: int = 5
    shortlist_n: int = 3


class RankedCandidate(BaseModel):
    item_id: int
    title: str
    per_user_scores: dict[int, float]
    composite_score: float


class TopPick(BaseModel):
    item_id: int
    title: str
    per_user_scores: dict[int, float]
    blurb: str


class RecommendationResponse(BaseModel):
    ranked: list[RankedCandidate]
    top_pick: TopPick | None
    log_id: int
