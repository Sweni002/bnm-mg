from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import Admin ,Client
from app.config import database
from app.utils.auth import verify_password, create_access_token
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Schema pour login via JSON
class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Chercher dans Admin
    user = db.query(Admin).filter(Admin.username == request.username).first()
    role = "admin"

    # Si pas trouvé, chercher dans Client
    if not user:
        user = db.query(Client).filter(Client.username == request.username).first()
        role = "client"

    # Vérification du mot de passe
    if not user or not user.verify_password(request.password):
        return error_response(message="Nom d'utilisateur ou mot de passe incorrect", status_code=401)

    # Générer le token
    access_token = create_access_token(data={"sub": user.username, "role": role})

    return success_response(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "role": role
        } ,
             message="Authentification  avec succès"
    )
