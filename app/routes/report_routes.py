from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from typing import List

from config.database import get_db
from app.models.baby_model import Baby
from app.models.event_model import Event
from app.models.daily_report_model import DailyReport
from app.dependencies.auth import get_current_user

# Importa os Schemas que você já possui
from app.schemas.report_schema import DailyReportResponse, DailyReportOut

router = APIRouter(prefix="/report", tags=["daily report"])


@router.post(
    "/generate",
    response_model=DailyReportResponse
)
def generate_daily_report(
    baby_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Gera ou atualiza o relatório diário para o bebê:
    - total_sleep_minutes: soma de todas as sonecas do dia (em minutos)
    - total_feeds: contagem de eventos com tipo 'feed' no dia
    - longest_nap_minutes: duração da maior soneca (em minutos)
    """
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    # 1) Confere se o bebê pertence ao usuário logado
    baby = (
        db.query(Baby)
        .filter_by(id=baby_id, user_id=current_user.id)
        .first()
    )
    if not baby:
        raise HTTPException(status_code=403, detail="Acesso negado para este bebê")

    # 2) Busca todos os eventos do dia para esse bebê
    events = (
        db.query(Event)
        .filter_by(baby_id=baby_id)
        .filter(Event.timestamp.between(start_of_day, end_of_day))
        .all()
    )
    if not events:
        raise HTTPException(status_code=400, detail="Nenhum evento encontrado para hoje")

    # 3) Calcula total de sono e maior soneca
    last_sleep = None
    total_sleep_minutes = 0
    longest_nap = 0

    for event in sorted(events, key=lambda e: e.timestamp):
        if event.type == "sleep_start":
            last_sleep = event.timestamp
        elif event.type == "sleep_end" and last_sleep:
            duration = int((event.timestamp - last_sleep).total_seconds() / 60)
            total_sleep_minutes += duration
            longest_nap = max(longest_nap, duration)
            last_sleep = None

    # 4) Conta quantos eventos de tipo 'feed' ocorreram no dia
    total_feeds = sum(1 for e in events if e.type == "feed")

    # 5) Prepara texto de notas (opcional, não faz parte da DailyReportResponse)
    notes_text = (
        f"Total de sono hoje: {total_sleep_minutes} minutos. "
        f"Maior soneca: {longest_nap} minutos. "
        f"Total de mamadas: {total_feeds}."
    )

    # 6) Verifica se já existe relatório para hoje e, se sim, atualiza; senão, cria novo
    existing_report = (
        db.query(DailyReport)
        .filter_by(baby_id=baby_id, date=today)
        .first()
    )

    if existing_report:
        existing_report.total_sleep_minutes = total_sleep_minutes
        existing_report.longest_nap_minutes = longest_nap
        existing_report.total_feeds = total_feeds
        existing_report.notes = notes_text
        db.commit()
        db.refresh(existing_report)
        report = existing_report
    else:
        report = DailyReport(
            baby_id=baby_id,
            date=today,
            total_sleep_minutes=total_sleep_minutes,
            longest_nap_minutes=longest_nap,
            total_feeds=total_feeds,
            notes=notes_text,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

    return {
        "total_sleep_minutes": report.total_sleep_minutes,
        "total_feeds": report.total_feeds,
        "longest_nap_minutes": report.longest_nap_minutes
    }


@router.get(
    "/daily",
    response_model=DailyReportResponse
)
def get_daily_report(
    baby_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retorna o relatório diário (hoje) para o bebê: 
    - total_sleep_minutes, total_feeds, longest_nap_minutes
    """
    today = date.today()
    baby = (
        db.query(Baby)
        .filter_by(id=baby_id, user_id=current_user.id)
        .first()
    )
    if not baby:
        raise HTTPException(status_code=403, detail="Acesso negado para este bebê")

    report = (
        db.query(DailyReport)
        .filter_by(baby_id=baby_id, date=today)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    return {
        "total_sleep_minutes": report.total_sleep_minutes,
        "total_feeds": report.total_feeds,
        "longest_nap_minutes": report.longest_nap_minutes
    }


@router.get(
    "/history",
    response_model=List[DailyReportOut]
)
def get_reports_history(
    baby_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retorna o histórico completo de DailyReport para um bebê,
    em ordem crescente de data, no formato:
      [{ "date": "YYYY-MM-DD", "total_sleep_minutes": X, "longest_nap_minutes": Y }, ...]
    """
    baby = (
        db.query(Baby)
        .filter_by(id=baby_id, user_id=current_user.id)
        .first()
    )
    if not baby:
        raise HTTPException(status_code=403, detail="Acesso negado para este bebê")

    reports = (
        db.query(DailyReport)
        .filter_by(baby_id=baby_id)
        .order_by(DailyReport.date.asc())
        .all()
    )

    history_list = []
    for r in reports:
        history_list.append({
            "date": r.date.isoformat(),  # retorna string "YYYY-MM-DD"
            "total_sleep_minutes": r.total_sleep_minutes,
            "longest_nap_minutes": r.longest_nap_minutes,
        })

    return history_list
