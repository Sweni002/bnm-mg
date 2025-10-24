# app/models/client.py
from sqlalchemy import Column, Integer, String
from .base import Base
from passlib.context import CryptContext

# ⚡ Utilisation d'Argon2 pour éviter la limite de 72 caractères et meilleure sécurité
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)

    # Hashage du mot de passe
    def set_password(self, password: str):
        if not password:
            raise ValueError("Le mot de passe ne peut pas être vide.")
        self.hashed_password = pwd_context.hash(password)

    # Vérification du mot de passe
    def verify_password(self, password: str) -> bool:
        if not self.hashed_password:
            return False
        return pwd_context.verify(password, self.hashed_password)
