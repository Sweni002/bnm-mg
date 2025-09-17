# app/schemas/admin.py
from pydantic import BaseModel, EmailStr

class AdminCreate(BaseModel):
    username: str
    email: EmailStr
    password: str  # mot de passe en clair à la création

class AdminResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True
