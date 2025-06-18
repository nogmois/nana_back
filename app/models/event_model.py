# app/models/event_model.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from config.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    baby_id = Column(Integer, ForeignKey("babies.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    baby = relationship("Baby", back_populates="events")


