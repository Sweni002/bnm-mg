from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.admin import Admin
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
    admin = db.query(Admin).filter(Admin.username == request.username).first()
    if not admin or not verify_password(request.password, admin.hashed_password):
        return error_response(message="Nom d'utilisateur ou mot de passe incorrect", status_code=401)

    access_token = create_access_token(data={"sub": admin.username})
    return success_response(data={"access_token": access_token, "token_type": "bearer"})
