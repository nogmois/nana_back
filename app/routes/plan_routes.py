from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date, time
from statistics import mean
from typing import List, Dict, Any

from app.models.sleep_plan_model import RoutinePlan
from app.models.event_model import Event
from app.models.baby_model import Baby
from app.dependencies.auth import get_current_user
from config.database import get_db
from app.utils.wake_window_calculator import get_wake_window_minutes

router = APIRouter(prefix="/plan", tags=["routine plan"])


def _get_historical_naps(
    baby_id: int,
    db: Session,
    days_back: int = 3
) -> List[Dict[str, datetime]]:
    """
    Busca eventos de sono (tipo "sleep_start"/"sleep_end") dos últimos 'days_back' dias
    e retorna pares de início/fim de soneca para cálculo de duração média.
    """
    cutoff = datetime.now() - timedelta(days=days_back)
    events = (
        db.query(Event)
        .filter(
            Event.baby_id == baby_id,
            Event.type.in_(("sleep_start", "sleep_end")),
            Event.timestamp >= cutoff
        )
        .order_by(Event.timestamp.asc())
        .all()
    )

    naps = []
    current_start = None
    for ev in events:
        if ev.type == "sleep_start":
            current_start = ev.timestamp
        elif ev.type == "sleep_end" and current_start:
            naps.append({"start": current_start, "end": ev.timestamp})
            current_start = None

    return naps


def _average_nap_duration(naps: List[Dict[str, datetime]], age_days: int) -> int:
    """
    Retorna a duração média em minutos. Se não houver histórico, usa uma estimativa baseada na idade.
    """
    if naps and len(naps) >= 2:
        durations = [(nap["end"] - nap["start"]).seconds // 60 for nap in naps]
        return int(mean(durations)) if durations else _nap_duration_fallback(age_days)
    return _nap_duration_fallback(age_days)



def _determine_naps_per_day(age_days: int) -> int:
    """
    Define quantas sonecas esperar em um dia, com base nas horas totais de sono diárias recomendadas.
    """
    if age_days <= 90:  # Recém-nascido (0–3 meses)
        return 6  # Vários ciclos curtos (~2–3h) ao longo do dia
    elif age_days <= 180:  # 3–6 meses
        return 4
    elif age_days <= 270:  # 6–9 meses
        return 3
    elif age_days <= 365:  # 9–12 meses
        return 2
    elif age_days <= 730:  # 1–2 anos
        return 1
    else:  # >2 anos
        return 1

    

def _nap_duration_fallback(age_days: int) -> int:
    """
    Duração estimada de cada soneca, baseada na quantidade de sono diário dividido pelo número de sonecas.
    """
    if age_days <= 90:
        return 90  # 6 sonecas de ~1h30
    elif age_days <= 180:
        return 90  # 4 sonecas de ~1h30
    elif age_days <= 270:
        return 90  # 3 sonecas de ~1h30
    elif age_days <= 365:
        return 90  # 2 sonecas de ~1h30
    elif age_days <= 730:
        return 120  # 1 soneca de 2h
    else:
        return 90  # >2 anos: 1 soneca de ~1h30




def _build_daily_routine(
    baby_id: int,
    last_sleep_end: datetime,
    avg_nap_minutes: int,
    current_date: date,
    naps_count: int,
    age_days: int,  
) -> Dict[str, Any]:
    """
    Gera o plano de rotina completo para 'naps_count' sonecas no dia 'current_date'.
    - Usa last_sleep_end como ponto de partida para first nap
    - Usa wake_window em minutos (pela idade) para calcular próxima soneca
    - Sonecas terão duração = avg_nap_minutes (fallback 45)
    - Cada mamada fica 15 min após o fim de uma soneca
    """

    # wake_window para a faixa etária do bebê
    wake_minutes = get_wake_window_minutes(age_days)

    naps_list: List[Dict[str, datetime]] = []
    feeds_list: List[datetime] = []

    now_dt = datetime.now()

    tentative_first_start = last_sleep_end + timedelta(minutes=wake_minutes)

    # Se o horário sugerido já passou, move a soneca para daqui 15 minutos
    if tentative_first_start < now_dt:
        tentative_first_start = now_dt + timedelta(minutes=15)

    first_start = tentative_first_start


    nap_start = first_start
    for i in range(naps_count):
        nap_end = nap_start + timedelta(minutes=avg_nap_minutes)
        feed_time = nap_end + timedelta(minutes=15)

        naps_list.append({"start": nap_start, "end": nap_end})
        feeds_list.append(feed_time)

        # Próxima soneca: wake window a partir do fim
        next_wake_minutes = wake_minutes
        nap_start = nap_end + timedelta(minutes=next_wake_minutes)

    return {
        "baby_id": baby_id,
        "date": naps_list[0]["start"].date(),
        "naps": naps_list,
        "feeds": feeds_list,
    }


@router.get("/today")
def get_today_plan(
    baby_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retorna o plano de rotina de hoje para esse bebê. Se já existir (e ainda não expirou),
    devolve. Caso contrário, gera um novo chamando generate_routine_plan.
    """
    baby = (
        db.query(Baby)
        .filter_by(id=baby_id, user_id=current_user.id)
        .first()
    )
    if not baby:
        raise HTTPException(status_code=403, detail="Acesso negado para este bebê")

    today = date.today()
    now = datetime.now()

    plan: RoutinePlan = (
        db.query(RoutinePlan)
        .filter_by(baby_id=baby_id, date=today)
        .first()
    )

    # Se já há um plano hoje e a primeira soneca ainda não terminou, retornamos
    if plan:
        last_sleep_end = (
            db.query(Event)
            .filter_by(baby_id=baby_id, type="sleep_end")
            .order_by(Event.timestamp.desc())
            .first()
        )

        if (
            last_sleep_end and
            plan.nap_start <= last_sleep_end.timestamp <= plan.nap_end
        ):
            # o bebê acordou dentro da soneca atual → plano ainda válido
            return {
                "baby_id": baby_id,
                "date": today,
                "naps": [{"start": plan.nap_start, "end": plan.nap_end}],
                "feeds": [plan.feed_time],
            }

        if not last_sleep_end and now < plan.nap_end:
            # fallback: nenhum evento ainda, plano ainda válido
            return {
                "baby_id": baby_id,
                "date": today,
                "naps": [{"start": plan.nap_start, "end": plan.nap_end}],
                "feeds": [plan.feed_time],
            }

        # Caso contrário, gera novo plano


    # Senão, chamamos a geração de rotina (que retornará JSON com várias sonecas/feeds)
    return generate_routine_plan(
        baby_id=baby_id,
        db=db,
        current_user=current_user
    )


@router.post("/routine/generate")
def generate_routine_plan(
    baby_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Gera (ou atualiza) um plano de rotina completo para o dia atual.
    Usa os últimos eventos + histórico de 3 dias para estimar duração média
    de soneca, quantidade de naps e wake-window pela idade.
    """
    # ------------------ validações básicas ------------------
    baby: Baby = (
        db.query(Baby)
        .filter_by(id=baby_id, user_id=current_user.id)
        .first()
    )
    if not baby:
        raise HTTPException(status_code=404, detail="Bebê não encontrado")

    last_sleep_event: Event = (
        db.query(Event)
        .filter(
            Event.baby_id == baby_id,
            Event.type.in_(["sleep_start", "sleep_end"])
        )
        .order_by(Event.timestamp.desc())
        .first()
    )
    if not last_sleep_event:
        raise HTTPException(
            status_code=400,
            detail="Nenhum evento de sono encontrado para esse bebê"
        )

    # ------------------ histórico e métricas ------------------
    historical_naps = _get_historical_naps(baby_id, db, days_back=3)
    age_in_days     = (date.today() - baby.birth_date).days
    avg_nap_minutes = _average_nap_duration(historical_naps, age_in_days)
    naps_count      = _determine_naps_per_day(age_in_days)

    # ------------------ ponto de partida ------------------
    if last_sleep_event.type == "sleep_start":
        # ainda dormindo → estimar fim
        last_sleep_end_dt = last_sleep_event.timestamp + timedelta(
            minutes=avg_nap_minutes
        )
    else:
        # já acordou
        last_sleep_end_dt = last_sleep_event.timestamp

    # ------------------ gerar rotina ------------------
    routine_date = date.today()
    routine = _build_daily_routine(
        baby_id=baby_id,
        last_sleep_end=last_sleep_end_dt,
        avg_nap_minutes=avg_nap_minutes,
        current_date=routine_date,
        naps_count=naps_count,
        age_days=age_in_days,            # wake-window correto
    )

    # ------------------ persistir primeira soneca ------------------
    first_nap  = routine["naps"][0]
    first_feed = routine["feeds"][0]

    existing: RoutinePlan = (
        db.query(RoutinePlan)
        .filter_by(baby_id=baby_id, date=first_nap["start"].date())
        .first()
    )
    if existing:
        existing.nap_start = first_nap["start"]
        existing.nap_end   = first_nap["end"]
        existing.feed_time = first_feed
    else:
        new_plan = RoutinePlan(
            baby_id=baby_id,
            date=first_nap["start"].date(),
            nap_start=first_nap["start"],
            nap_end=first_nap["end"],
            feed_time=first_feed,
        )
        db.add(new_plan)

    db.commit()

    # ------------------ resposta ------------------
    return {
        "baby_id": baby_id,
        "date": routine_date,
        "naps": routine["naps"],
        "feeds": routine["feeds"],
    }


