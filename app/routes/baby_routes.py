from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.baby_model import Baby
from app.models.auth_models import User
from app.schemas.baby_schema import BabyCreate, BabyUpdate, BabyResponse
from config.database import get_db
from app.dependencies.auth import get_current_user
from typing import List

router = APIRouter(prefix="/babies", tags=["babies"])

# POST: cria novo bebê
@router.post("")
def create_baby(
    baby: BabyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_baby = Baby(
        user_id=current_user.id,
        name=baby.name,
        birth_date=baby.birth_date,
        birth_weight_grams=baby.birth_weight_grams,
        gender=baby.gender   
    )
    db.add(new_baby)
    db.commit()
    db.refresh(new_baby)

    return {
        "msg": "Bebê cadastrado com sucesso.",
        "baby_id": new_baby.id,
        "name": new_baby.name
    }

# GET: busca os bebês do usuário logado
@router.get("/me", response_model=List[BabyResponse])
def get_my_babies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    babies = db.query(Baby).filter(Baby.user_id == current_user.id).all()
    return babies

# PUT: atualiza um bebê específico (se for do usuário)
@router.put("/{baby_id}", response_model=BabyResponse)
def update_baby(
    baby_id: int,
    baby_data: BabyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    baby = db.query(Baby).filter_by(id=baby_id, user_id=current_user.id).first()
    if not baby:
        raise HTTPException(status_code=404, detail="Bebê não encontrado.")

    baby.name = baby_data.name or baby.name
    baby.birth_date = baby_data.birth_date or baby.birth_date
    baby.birth_weight_grams = baby_data.birth_weight_grams or baby.birth_weight_grams

    db.commit()
    db.refresh(baby)
    return baby
