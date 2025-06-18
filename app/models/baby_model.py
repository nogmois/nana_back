from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base

class Baby(Base):
    __tablename__ = "babies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # FK para o pai/mãe
    name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    birth_weight_grams = Column(Integer, nullable=True)  # opcional
    gender = Column(String(6), nullable=False)

    parent = relationship("User", back_populates="babies")
    events = relationship("Event", back_populates="baby", cascade="all, delete")

    sleep_plans = relationship("SleepPlan", back_populates="baby", cascade="all, delete")
