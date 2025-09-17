# app/schemas/client.py
from pydantic import BaseModel, EmailStr

class ClientCreate(BaseModel):
    username: str
    email: EmailStr
    password: str  # mot de passe en clair à la création

class ClientResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True
