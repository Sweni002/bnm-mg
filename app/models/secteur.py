from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class Secteur(Base):
    __tablename__ = "secteurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), unique=True, nullable=False)

    # Relation 1-n avec Norme
    normes = relationship("Norme", back_populates="secteur")
