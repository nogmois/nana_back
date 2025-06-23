# src/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import stripe
import os
from datetime import datetime, timedelta
from config.database import get_db
from app.models.auth_models import User
from app.schemas.auth_schema import AuthRequest  # seu Pydantic model
from app.utils.magic import jwt_for_user

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# configure sua chave secreta do Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/cadastro", status_code=status.HTTP_201_CREATED)
def signup(data: AuthRequest, db: Session = Depends(get_db)):
    # 1) Verifica se já existe usuário
    existing_user = db.query(User).filter_by(email=data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado."
        )

    # 2) Cria o customer no Stripe
    try:
        customer = stripe.Customer.create(
            email=data.email,
            metadata={"app": "nanafacil", "user_email": data.email}
        )
    except stripe.error.StripeError as e:
        # opcional: logar e retornar erro mais genérico
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível criar perfil de pagamento."
        )

    # 3) Cria o usuário no banco local
    hashed_password = pwd_context.hash(data.password)
    user = User(
        email=data.email,
        password_hash=hashed_password,
        stripe_customer_id=customer.id  # grava o ID do Stripe
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "msg": "Usuário criado com sucesso.",
        "user_id": user.id,
        "email": user.email
    }

@router.post("/login")
def login(data: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    # JWT…
    token = jwt_for_user(email=user.email, role=user.role)

    # Assinatura ativa?
    subs = stripe.Subscription.list(
        customer=user.stripe_customer_id, status="active", limit=1
    )
    has_active = len(subs.data) > 0

    # Trial de 3 dias
    trial_end_dt = user.created_at + timedelta(days=3)
    now = datetime.utcnow()
    trial_active = now < trial_end_dt

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "stripe_customer_id": user.stripe_customer_id,
        "has_active_subscription": has_active,
        "trial_active": trial_active,
        "trial_end": trial_end_dt.isoformat(),
        "role": user.role,
    }
