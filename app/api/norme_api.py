from fastapi import APIRouter, Depends, UploadFile, File ,Form , Request
from sqlalchemy.orm import Session 
from sqlalchemy.exc import IntegrityError
from pathlib import Path
from shutil import copyfileobj
from datetime import date
from app.models.norme import Norme
from app.models.secteur import Secteur
from app.config.database import SessionLocal
from app.utils.response import success_response, error_response
from datetime import datetime, date
from fastapi.responses  import FileResponse , StreamingResponse
from fastapi import UploadFile, HTTPException
from pdf2image import convert_from_bytes
import pytesseract
import re
import io
from app.utils.auth import decode_access_token
import os

router = APIRouter(prefix="/normes", tags=["Normes"])

UPLOAD_DIR = Path("uploads/pdf")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
async def create_norme(
    codification: str = Form(...),
    nom: str = Form(...),
    date_creation: str = Form(...),
    secteur_id: int = Form(...),
    nbrepage: int = Form(...),          # <-- nouveau paramètre
    fichier_pdf: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    print("codification:", codification)
    print("nom:", nom)
    print("nbrepage:", nbrepage, type(nbrepage))
    print("date_creation:", date_creation)
    print("secteur_id:", secteur_id, type(secteur_id))
    print("fichier_pdf:", fichier_pdf.filename if fichier_pdf else None)

    try:
        # Vérifier l'extension PDF
        if not fichier_pdf.filename.lower().endswith(".pdf"):
            return error_response(message="Le fichier doit être un PDF", status_code=400)

        # Vérifier si le secteur existe
        secteur = db.query(Secteur).filter(Secteur.id == secteur_id).first()
        if not secteur:
            return error_response(message="Secteur non trouvé", status_code=404)

        # Sauvegarder le fichier
        file_path = UPLOAD_DIR / fichier_pdf.filename
        with file_path.open("wb") as buffer:
            copyfileobj(fichier_pdf.file, buffer)

        # Créer l'objet Norme
        db_norme = Norme(
            codification=codification,
            nom=nom,
            nbrepage=nbrepage,               # <-- inclure ici
            date_creation=date_creation,
            secteur_id=secteur_id,
            fichier_pdf=str(file_path)
        )
        db.add(db_norme)
        db.commit()
        db.refresh(db_norme)

        return success_response(
    data={
        "id": db_norme.id,
        "codification": db_norme.codification,
        "nbrepage":db_norme.nbrepage,
        "nom": db_norme.nom,
        "date_creation": db_norme.date_creation ,  # <- convertir en string
        "fichier_pdf": db_norme.fichier_pdf,
        "secteur": {"id": secteur.id, "nom": secteur.nom}
    },
    message="Norme créée avec succès"
)
    except IntegrityError:
           db.rollback()
           return error_response(message=f"La codification '{codification}' existe déjà", status_code=400)

@router.post("/pdf/get_nbre")
async def get_last_page_number_ocr(file: UploadFile = File(...)):
    # Vérifie l'extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")
    
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Fichier PDF vide")
        
        # Convertir PDF en images
        images = convert_from_bytes(contents)
        if not images:
            raise HTTPException(status_code=500, detail="Impossible de convertir le PDF en images")
        
        last_page_number = 0
        
        # Parcours de toutes les pages
        for i, img in enumerate(images):
            # OCR pour extraire le texte
            text = pytesseract.image_to_string(img)
            
            # Cherche tous les nombres dans le texte
            numbers = re.findall(r'\b\d+\b', text)
            
            # Met à jour le dernier numéro de page trouvé
            if numbers:
                num = int(numbers[-1])
                if num > last_page_number:
                    last_page_number = num
        
        if last_page_number == 0:
            # Aucun numéro détecté, renvoyer le nombre de pages réel
            last_page_number = len(images)
        
        return {"filename": file.filename, "last_page_number": last_page_number}

    except Exception as e:
        # Affichage debug dans la console
        print("Erreur OCR PDF:", e)
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du PDF: {str(e)}")
  
# ----------------- Lire tous les Normes -----------------
@router.get("/")
def read_normes(db: Session = Depends(get_db)):
    normes = db.query(Norme).all()
    data = [
        {
            "id": n.id,
            "codification": n.codification,
            "nom": n.nom,
            'nbrepage': n.nbrepage ,
            "date_creation": n.date_creation ,
            "fichier_pdf": n.fichier_pdf,
            "secteur": {
                "id": n.secteur.id,
                "nom": n.secteur.nom
            } if n.secteur else None
        }
        for n in normes
    ]
    return success_response(data=data)


# ----------------- Lire tous les Normes -----------------
@router.get("/")
def read_normes(db: Session = Depends(get_db)):
    normes = db.query(Norme).order_by(Norme.codification.asc()).all()  # tri A → Z
    data = [
        {
            "id": n.id,
            "codification": n.codification,
            "nom": n.nom,
              'nbrepage': n.nbrepage ,

            "date_creation": n.date_creation ,
            "fichier_pdf": n.fichier_pdf,
            "secteur": {
                "id": n.secteur.id,
                "nom": n.secteur.nom
            } if n.secteur else None
        }
        for n in normes
    ]
    return success_response(data=data)

@router.get("/count")
def count_normes(db: Session = Depends(get_db)):
    """Retourne le nombre total de normes."""
    total = db.query(Norme).count()
    return success_response(data={"total_normes": total})

@router.get("/secteur/{secteur_id}")
def read_normes_by_secteur(secteur_id: int, db: Session = Depends(get_db)):
    normes = (
        db.query(Norme)
        .filter(Norme.secteur_id == secteur_id)
        .order_by(Norme.codification.asc())  # tri alphabétique
        .all()
    )

    data = [
        {
            "id": n.id,
            "codification": n.codification,
            "nom": n.nom,
            "date_creation": n.date_creation ,
            "fichier_pdf": n.fichier_pdf,
            "secteur": {
                "id": n.secteur.id,
                "nom": n.secteur.nom
            } if n.secteur else None
        }
        for n in normes
    ]
    return success_response(data=data)

# ----------------- Lire une Norme -----------------
@router.get("/{norme_id}")
def read_norme(norme_id: int, db: Session = Depends(get_db)):
    db_norme = db.query(Norme).filter(Norme.id == norme_id).first()
    if not db_norme:
        return error_response(message="Norme non trouvée", status_code=404)

    return success_response(
        data={
            "id": db_norme.id,
            "codification": db_norme.codification,
            "nom": db_norme.nom,
            "date_creation": db_norme.date_creation,
            "fichier_pdf": db_norme.fichier_pdf,
            "secteur": {
                "id": db_norme.secteur.id,
                "nom": db_norme.secteur.nom
            } if db_norme.secteur else None
        }
    )

# ----------------- Supprimer une Norme -----------------
@router.delete("/{norme_id}")
def delete_norme(norme_id: int, db: Session = Depends(get_db)):
    db_norme = db.query(Norme).filter(Norme.id == norme_id).first()
    if not db_norme:
        return error_response(message="Norme non trouvée", status_code=404)

    # Supprimer le fichier PDF
    try:
        pdf_path = Path(db_norme.fichier_pdf)
        if pdf_path.exists():
            pdf_path.unlink()
    except Exception as e:
        return error_response(message=f"Erreur lors de la suppression du PDF: {e}", status_code=500)

    # Supprimer la norme de la DB
    db.delete(db_norme)
    db.commit()

    return success_response(
        data={"id": db_norme.id, "codification": db_norme.codification},
        message="Norme supprimée avec succès"
    )

@router.put("/{norme_id}")
async def update_norme(
    norme_id: int,
    codification: str = Form(...),
    nom: str = Form(...),
    date_creation: str = Form(...),
    secteur_id: int = Form(...),
    nbrepage: int = Form(...),
    fichier_pdf: UploadFile = File(None),  # PDF optionnel lors de la mise à jour
    db: Session = Depends(get_db)
):
    # Vérifier si la norme existe
    db_norme = db.query(Norme).filter(Norme.id == norme_id).first()
    if not db_norme:
        return error_response(message="Norme non trouvée", status_code=404)

    # Vérifier si la codification est déjà utilisée par une autre norme
    norme_exist = db.query(Norme).filter(Norme.codification == codification, Norme.id != norme_id).first()
    if norme_exist:
        return error_response(message=f"La codification '{codification}' existe déjà", status_code=400)

    # Vérifier si le secteur existe
    secteur = db.query(Secteur).filter(Secteur.id == secteur_id).first()
    if not secteur:
        return error_response(message="Secteur non trouvé", status_code=404)

    try:
        # Si un nouveau fichier PDF est envoyé, le sauvegarder
        if fichier_pdf:
            if not fichier_pdf.filename.lower().endswith(".pdf"):
                return error_response(message="Le fichier doit être un PDF", status_code=400)

            file_path = UPLOAD_DIR / fichier_pdf.filename
            with file_path.open("wb") as buffer:
                copyfileobj(fichier_pdf.file, buffer)

            db_norme.fichier_pdf = str(file_path)

        # Mettre à jour les champs
        db_norme.codification = codification
        db_norme.nom = nom
        db_norme.nbrepage = nbrepage
        db_norme.date_creation = date_creation
        db_norme.secteur_id = secteur_id

        db.commit()
        db.refresh(db_norme)

        return success_response(
            data={
                "id": db_norme.id,
                "codification": db_norme.codification,
                "nbrepage": db_norme.nbrepage,
                "nom": db_norme.nom,
                "date_creation": db_norme.date_creation,
                "fichier_pdf": db_norme.fichier_pdf,
                "secteur": {"id": secteur.id, "nom": secteur.nom}
            },
            message="Norme mise à jour avec succès"
        )

    except IntegrityError:
        db.rollback()
        return error_response(message="Erreur lors de la mise à jour", status_code=400)
 
    
@router.get("/{norme_id}/pdf")
def view_norme_pdf(norme_id: int, db: Session = Depends(get_db)):
    db_norme = db.query(Norme).filter(Norme.id == norme_id).first()
    if not db_norme:
        return error_response(message="Norme non trouvée", status_code=404)

    pdf_path = Path(db_norme.fichier_pdf)
    if not pdf_path.exists():
        return error_response(message="Fichier PDF introuvable", status_code=404)

    # FileResponse va afficher le PDF directement dans le navigateur
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf"
        # pas de "filename" ici pour éviter le téléchargement automatique
    )



def get_current_user(request: Request):
    token = request.headers.get("Authorization")
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