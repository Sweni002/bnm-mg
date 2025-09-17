from pydantic import BaseModel
from typing import List
from app.schemas.norme import NormeResponse

class SecteurBase(BaseModel):
    nom: str

class SecteurCreate(BaseModel):
    nom: str

class SecteurResponse(SecteurBase):
    id: int
    normes: List[NormeResponse] = []

    class Config:
        orm_mode = True
