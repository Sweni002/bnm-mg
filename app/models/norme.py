from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Norme(Base):
    __tablename__ = "normes"

    id = Column(Integer, primary_key=True, index=True)
    codification = Column(String(255), unique=True, nullable=False)
    nom = Column(String(200), nullable=False)
    date_creation = Column(Date, nullable=False)

    # chemin du fichier PDF
    fichier_pdf = Column(String(255), nullable=False)

    secteur_id = Column(Integer, ForeignKey("secteurs.id"), nullable=False)
    secteur = relationship("Secteur", back_populates="normes")
