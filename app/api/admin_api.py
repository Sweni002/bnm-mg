from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.admin import Admin
from app.schemas.admin import AdminCreate
from app.config.database import SessionLocal
from app.utils.response import success_response, error_response
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/admins", tags=["Admins"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_admin(admin: AdminCreate, db: Session = Depends(get_db)):
    # Vérifier que les champs ne sont pas vides
    if not admin.username or not admin.email or not admin.password:
        return error_response(message="Tous les champs sont obligatoires", status_code=400)

    db_admin = Admin(username=admin.username, email=admin.email)
    db_admin.hashed_password = pwd_context.hash(admin.password)

    try:
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)
        return success_response(
            data={"id": db_admin.id, "username": db_admin.username, "email": db_admin.email},
            message="Admin créé avec succès"
        )
    except IntegrityError:
        db.rollback()
        return error_response(message="Username ou email déjà existant", status_code=400)
    except Exception as e:
        db.rollback()
        return error_response(message=f"Erreur serveur: {e}", status_code=500)

@router.get("/{admin_id}")
def read_admin(admin_id: int, db: Session = Depends(get_db)):
    db_admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not db_admin:
        return error_response(message="Admin non trouvé", status_code=404)
    return success_response(
        data={"id": db_admin.id, "username": db_admin.username, "email": db_admin.email}
    )


@router.get("/")
def read_admins(db: Session = Depends(get_db)):
    admins = db.query(Admin).all()
    data = [{"id": a.id, "username": a.username, "email": a.email} for a in admins]
    return success_response(data=data)


@router.delete("/{admin_id}")
def delete_admin(admin_id: int, db: Session = Depends(get_db)):
    db_admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not db_admin:
        return error_response(message="Admin non trouvé", status_code=404)
    db.delete(db_admin)
    db.commit()
    return success_response(
        data={"id": db_admin.id, "username": db_admin.username, "email": db_admin.email},
        message="Admin supprimé avec succès"
    )
