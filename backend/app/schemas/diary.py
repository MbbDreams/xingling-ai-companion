from datetime import date, datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class DiaryCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    mood: str = "calm"
    user_id: int | None = None
    companion_id: int | None = None
    happened_on: date | None = Field(default=None, alias="happened_on")
    tags: list[str] = Field(default_factory=list)
    
    model_config = ConfigDict(populate_by_name=True)


class DiaryRead(BaseModel):
    id: int
    user_id: int
    companion_id: int | None = None
    mood: str
    content: str
    summary: str | None = None
    happened_on: date
    tags: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiaryCalendarItem(BaseModel):
    day: int
    mood: str
    has_diary: bool = True


class DiaryCalendarResponse(BaseModel):
    year: int
    month: int
    days: list[DiaryCalendarItem] = Field(alias="dates")
    
    model_config = ConfigDict(populate_by_name=True)
