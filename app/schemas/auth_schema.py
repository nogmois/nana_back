from pydantic import BaseModel, EmailStr

# Modelo para cadastro e login
class AuthRequest(BaseModel):
    email: EmailStr
    password: str
