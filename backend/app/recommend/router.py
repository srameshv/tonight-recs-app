from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.recommend.schemas import RecommendationRequest, RecommendationResponse
from app.recommend.service import build_recommendations

router = APIRouter()


@router.post("/recommendations", response_model=RecommendationResponse)
def recommend(
    request: RecommendationRequest, session: Session = Depends(get_session)
):
    try:
        return build_recommendations(session, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
