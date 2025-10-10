from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.utils.auth import decode_access_token
import os
from app.models.norme import Norme
from app.config.database import SessionLocal
from sqlalchemy.orm import Session 

router = APIRouter(prefix="/pdf", tags=["Pdf"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dépendance pour récupérer l'utilisateur depuis le token
def get_current_user(token: str = Depends(lambda request: request.headers.get("Authorization"))):
    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")
    token = token.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    return payload

@router.get("/view_pdf/{norme_id}")
async def view_pdf(norme_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    norme = db.query(Norme).filter(Norme.id == norme_id).first()
    if not norme:
        raise HTTPException(status_code=404, detail="Norme introuvable")
    
    pdf_path = norme.fichier_pdf
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Fichier PDF non trouvé")
    
    file = open(pdf_path, "rb")
    return StreamingResponse(file, media_type="application/pdf")
