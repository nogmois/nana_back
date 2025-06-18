# app/schemas/event_schema.py

from pydantic import BaseModel
from datetime import datetime

class EventCreate(BaseModel):
    baby_id: int
    type: str
    timestamp: datetime

    class Config:
        orm_mode = True

class EventUpdate(BaseModel):
    type: str | None = None
    timestamp: datetime | None = None

class EventRead(BaseModel):
    id: int
    baby_id: int
    type: str
    timestamp: datetime

    class Config:
        orm_mode = True
