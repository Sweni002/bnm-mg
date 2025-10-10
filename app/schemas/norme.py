from pydantic import BaseModel
from datetime import date

class NormeBase(BaseModel):
    codification: str
    nom: str
    nbrepage: int
    date_creation: str
    fichier_pdf: str
    secteur_id: int

class NormeCreate(NormeBase):
    pass

class NormeResponse(NormeBase):
    id: int
    secteur: dict  # juste un dict avec id et nom du secteur

    class Config:
        orm_mode = True
