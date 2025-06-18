from pydantic import BaseModel
from datetime import date
from typing import Optional

class BabyCreate(BaseModel):
    name: str
    birth_date: date
    birth_weight_grams: Optional[int] = None
    gender: str                         # novo campo

class BabyUpdate(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[date] = None
    birth_weight_grams: Optional[int] = None
    gender: Optional[str] = None

class BabyResponse(BaseModel):
    id: int
    name: str
    birth_date: date
    birth_weight_grams: Optional[int]
    gender: str                         # retorna o sexo

    class Config:
        orm_mode = True
