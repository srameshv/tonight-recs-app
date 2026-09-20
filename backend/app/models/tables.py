from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import JSON, Column, Field, SQLModel


class ItemType(str, Enum):
    movie = "movie"
    tv = "tv"
    restaurant = "restaurant"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: ItemType
    external_id: str
    title: str
    item_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))


class Rating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    item_id: int = Field(foreign_key="item.id")
    value: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PreferenceNote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    text: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RecommendationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    context: dict = Field(default_factory=dict, sa_column=Column(JSON))
    results: dict = Field(default_factory=dict, sa_column=Column(JSON))
