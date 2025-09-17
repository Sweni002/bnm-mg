from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.client import Client
from app.schemas.client import ClientCreate
from app.config.database import SessionLocal
from app.utils.response import success_response, error_response
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/clients", tags=["Clients"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    db_client = Client(username=client.username, email=client.email)
    db_client.hashed_password = pwd_context.hash(client.password)
    try:
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return success_response(
            data={"id": db_client.id, "username": db_client.username, "email": db_client.email},
            message="Client créé avec succès"
        )
    except IntegrityError:
        db.rollback()
        return error_response(message="Username ou email déjà existant", status_code=400)


@router.get("/{client_id}")
def read_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
        return error_response(message="Client non trouvé", status_code=404)
    return success_response(
        data={"id": db_client.id, "username": db_client.username, "email": db_client.email}
    )


@router.get("/")
def read_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    data = [{"id": c.id, "username": c.username, "email": c.email} for c in clients]
    return success_response(data=data)


@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
        return error_response(message="Client non trouvé", status_code=404)
    db.delete(db_client)
    db.commit()
    return success_response(
        data={"id": db_client.id, "username": db_client.username, "email": db_client.email},
        message="Client supprimé avec succès"
    )



@router.put("/{client_id}")
def update_client(client_id: int, client: ClientCreate, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
        return error_response(message="Client non trouvé", status_code=404)

    # Vérifier si le username existe pour un autre client
    existing_username = db.query(Client).filter(Client.username == client.username, Client.id != client_id).first()
    if existing_username:
        return error_response(message="Username déjà utilisé", status_code=400)

    # Vérifier si l'email existe pour un autre client
    existing_email = db.query(Client).filter(Client.email == client.email, Client.id != client_id).first()
    if existing_email:
        return error_response(message="Email déjà utilisé", status_code=400)

    # Mise à jour
    db_client.username = client.username
    db_client.email = client.email
    db_client.hashed_password = pwd_context.hash(client.password)

    db.commit()
    db.refresh(db_client)

    return success_response(
        data={
            "id": db_client.id,
            "username": db_client.username,
            "email": db_client.email
        },
        message="Client mis à jour avec succès"
    )
