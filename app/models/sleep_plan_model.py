# app/models/sleep_plan_model.py

from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, func
from sqlalchemy.orm import relationship
from config.database import Base

class SleepPlan(Base):
    __tablename__ = "sleep_plans"

    id = Column(Integer, primary_key=True)
    baby_id = Column(Integer, ForeignKey("babies.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    suggested_nap_start = Column(DateTime, nullable=True)
    suggested_nap_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relacionamento com o modelo Baby (opcional, mas útil)
    baby = relationship("Baby", back_populates="sleep_plans")


class RoutinePlan(Base):
    __tablename__ = "routine_plans"

    id = Column(Integer, primary_key=True)
    baby_id = Column(Integer, ForeignKey("babies.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)

    nap_start = Column(DateTime, nullable=True)
    nap_end = Column(DateTime, nullable=True)

    feed_time = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())