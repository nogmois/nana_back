# src/routers/payment.py

import stripe
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.auth_models import User
from config.database import get_db
from app.dependencies.auth import get_current_user

import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
router = APIRouter(prefix="/payment")

@router.post("/checkout-session")
def create_checkout_session(
    data: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    price_id = data.get("priceId")
    if not price_id:
        raise HTTPException(status_code=400, detail="Price ID obrigatório.")
    session = stripe.checkout.Session.create(
        customer=user.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url="https://nanafacil-web.onrender.com/success",
        cancel_url="https://nanafacil-web.onrender.com/plans",
    )
    return {"sessionId": session.id}
