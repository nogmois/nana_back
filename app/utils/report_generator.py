# app/utils/report_generator.py

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.event_model import Event

def generate_daily_summary(db: Session, baby_id: int, date: datetime.date):
    # Define intervalo do dia (00:00 às 23:59)
    day_start = datetime.combine(date, datetime.min.time())
    day_end = datetime.combine(date, datetime.max.time())

    events = db.query(Event).filter(
        Event.baby_id == baby_id,
        Event.timestamp >= day_start,
        Event.timestamp <= day_end
    ).order_by(Event.timestamp).all()

    total_sleep = timedelta()
    total_feeds = 0
    longest_nap = timedelta()
    last_sleep_start = None

    for event in events:
        if event.type == "sleep_start":
            last_sleep_start = event.timestamp
        elif event.type == "sleep_end" and last_sleep_start:
            duration = event.timestamp - last_sleep_start
            total_sleep += duration
            if duration > longest_nap:
                longest_nap = duration
            last_sleep_start = None
        elif event.type == "feed":
            total_feeds += 1

    return {
        "total_sleep_minutes": int(total_sleep.total_seconds() / 60),
        "total_feeds": total_feeds,
        "longest_nap_minutes": int(longest_nap.total_seconds() / 60),
    }
