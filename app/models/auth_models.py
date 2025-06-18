from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from config.database import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String)  # <- nova coluna
    stripe_customer_id = Column(String, unique=True, nullable=True)

    role = Column(String, default="parent", nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # No User model
    babies = relationship("Baby", back_populates="parent")



class MagicToken(Base):
    __tablename__ = "magic_tokens"
    id        = Column(Integer, primary_key=True)
    email     = Column(String, index=True, nullable=False)
    token     = Column(String, unique=True, nullable=False)
    expires   = Column(DateTime, nullable=False)
    used      = Column(Boolean, default=False)
