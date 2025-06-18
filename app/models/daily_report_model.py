from sqlalchemy import Column, Integer, Date, ForeignKey, Text, func
from config.database import Base

class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True)
    baby_id = Column(Integer, ForeignKey("babies.id", ondelete="CASCADE"))
    date = Column(Date, nullable=False)
    total_sleep_minutes = Column(Integer)
    longest_nap_minutes = Column(Integer)
    total_feeds = Column(Integer, nullable=False, default=0) 
    notes = Column(Text)
    created_at = Column(Date, server_default=func.now())
