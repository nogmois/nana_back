from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from config.database import get_db
from app.models.event_model import Event
from app.models.baby_model import Baby
from app.models.auth_models import User

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/events-per-mother")
def events_per_mother(db: Session = Depends(get_db)):
    results = (
        db.query(
            User.id.label("user_id"),
            User.email.label("mother_email"),
            func.count(Event.id).label("event_count"),
        )
        .join(Baby, Baby.user_id == User.id)
        .join(Event, Event.baby_id == Baby.id)
        .group_by(User.id, User.email)
        .all()
    )

    return [
        {
            "user_id":    row.user_id,
            "mother_email": row.mother_email,
            "event_count": row.event_count,
        }
        for row in results
    ]
