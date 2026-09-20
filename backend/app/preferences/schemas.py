from app.models.tables import ItemType
from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    name: str


class ItemOut(BaseModel):
    id: int
    type: ItemType
    title: str
    item_metadata: dict


class RatingIn(BaseModel):
    user_id: int
    item_id: int
    value: int


class RatingOut(RatingIn):
    id: int


class PreferenceNoteIn(BaseModel):
    user_id: int
    text: str


class PreferenceNoteOut(PreferenceNoteIn):
    id: int
