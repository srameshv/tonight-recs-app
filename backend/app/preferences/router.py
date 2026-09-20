from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models import Item, ItemType, PreferenceNote, Rating, User
from app.preferences.schemas import (
    ItemOut,
    PreferenceNoteIn,
    PreferenceNoteOut,
    RatingIn,
    RatingOut,
    UserOut,
)

router = APIRouter()


@router.get("/users", response_model=list[UserOut])
def list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()


@router.get("/items", response_model=list[ItemOut])
def list_items(
    type: Optional[ItemType] = Query(default=None),
    session: Session = Depends(get_session),
):
    statement = select(Item)
    if type is not None:
        statement = statement.where(Item.type == type)
    return session.exec(statement).all()


@router.get("/ratings", response_model=list[RatingOut])
def list_ratings(user_id: int, session: Session = Depends(get_session)):
    return session.exec(select(Rating).where(Rating.user_id == user_id)).all()


@router.post("/ratings", response_model=RatingOut)
def upsert_rating(payload: RatingIn, session: Session = Depends(get_session)):
    if not session.get(User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if not session.get(Item, payload.item_id):
        raise HTTPException(status_code=404, detail="Item not found")

    existing = session.exec(
        select(Rating).where(
            Rating.user_id == payload.user_id,
            Rating.item_id == payload.item_id,
        )
    ).first()
    if existing:
        existing.value = payload.value
        existing.created_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    rating = Rating(**payload.model_dump())
    session.add(rating)
    session.commit()
    session.refresh(rating)
    return rating


@router.get("/preferences/notes/{user_id}", response_model=Optional[PreferenceNoteOut])
def get_note(user_id: int, session: Session = Depends(get_session)):
    return session.exec(
        select(PreferenceNote).where(PreferenceNote.user_id == user_id)
    ).first()


@router.put("/preferences/notes", response_model=PreferenceNoteOut)
def upsert_note(payload: PreferenceNoteIn, session: Session = Depends(get_session)):
    if not session.get(User, payload.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    existing = session.exec(
        select(PreferenceNote).where(PreferenceNote.user_id == payload.user_id)
    ).first()
    if existing:
        existing.text = payload.text
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    note = PreferenceNote(**payload.model_dump())
    session.add(note)
    session.commit()
    session.refresh(note)
    return note
