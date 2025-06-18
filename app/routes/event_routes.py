from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.models.event_model import Event
from app.models.auth_models import User
from app.schemas.event_schema import EventCreate, EventUpdate, EventRead
from config.database import get_db
from app.dependencies.auth import get_current_user
from typing import List, Union

router = APIRouter(prefix="/events", tags=["events"])

@router.post("", status_code=201)
def create_event(
    # Aqui estamos dizendo: o body pode ser um único EventCreate ou uma lista de EventCreate.
    events: Union[EventCreate, List[EventCreate]] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Se receber um objeto único (EventCreate), cria um único registro.
    Se receber uma lista de EventCreate, cria múltiplos registros em batch.
    """

    # Vamos padronizar uma lista de eventos a ser processada:
    if isinstance(events, list):
        event_list = events
    else:
        event_list = [events]

    created = []  # para retornar dados de cada evento criado

    for ev_data in event_list:

        new_event = Event(
            user_id=current_user.id,
            baby_id=ev_data.baby_id,
            type=ev_data.type,
            timestamp=ev_data.timestamp,
        )
        db.add(new_event)
        db.flush()  # garante que new_event.id seja atribuído antes do commit
        created.append({"event_id": new_event.id, "type": new_event.type})

    db.commit()

    return {
        "msg": "Eventos registrados com sucesso.",
        "created": created,
    }

@router.get("", response_model=List[EventRead])
def list_events(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    events = db.query(Event).filter(Event.user_id == current_user.id).order_by(Event.timestamp.desc()).all()
    return events

@router.put("/{event_id}")
def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    event = db.query(Event).filter_by(id=event_id, user_id=current_user.id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    event.type = event_update.type or event.type
    event.timestamp = event_update.timestamp or event.timestamp

    db.commit()
    db.refresh(event)

    return {
        "msg": "Evento atualizado com sucesso.",
        "event_id": event.id,
        "type": event.type,
        "timestamp": event.timestamp
    }


@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    event = db.query(Event).filter_by(id=event_id, user_id=current_user.id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Evento não encontrado.")

    db.delete(event)
    db.commit()

    return {"msg": "Evento excluído com sucesso."}