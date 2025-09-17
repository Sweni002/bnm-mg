from fastapi import APIRouter, Depends, UploadFile, File ,Form
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
    date_creation: date = Form(...),
    secteur_id: int = Form(...),
    fichier_pdf: UploadFile = File(...),
    db: Session = Depends(get_db)
):
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
        "nom": db_norme.nom,
        "date_creation": db_norme.date_creation.isoformat(),  # <- convertir en string
        "fichier_pdf": db_norme.fichier_pdf,
        "secteur": {"id": secteur.id, "nom": secteur.nom}
    },
    message="Norme créée avec succès"
)
    except IntegrityError:
           db.rollback()
           return error_response(message=f"La codification '{codification}' existe déjà", status_code=400)

      
# ----------------- Lire tous les Normes -----------------
@router.get("/")
def read_normes(db: Session = Depends(get_db)):
    normes = db.query(Norme).all()
    data = [
        {
            "id": n.id,
            "codification": n.codification,
            "nom": n.nom,
            "date_creation": n.date_creation.isoformat() if n.date_creation else None,
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
            "date_creation": db_norme.date_creation.isoformat() if db_norme.date_creation else None,
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
    codification: str = Form(None),
    nom: str = Form(None),
    date_creation: str = Form(None),  # on convertira en date ensuite
    secteur_id: int = Form(None),
    fichier_pdf: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    db_norme = db.query(Norme).filter(Norme.id == norme_id).first()
    if not db_norme:
        return error_response(message="Norme non trouvée", status_code=404)

    if codification:
        db_norme.codification = codification.strip()
    if nom:
        db_norme.nom = nom.strip()
    if date_creation:
        db_norme.date_creation = datetime.strptime(date_creation, "%Y-%m-%d").date()
    if secteur_id:
        secteur = db.query(Secteur).filter(Secteur.id == secteur_id).first()
        if not secteur:
            return error_response(message="Secteur non trouvé", status_code=404)
        db_norme.secteur_id = secteur_id

    if fichier_pdf:
        if not fichier_pdf.filename.lower().endswith(".pdf"):
            return error_response(message="Le fichier doit être un PDF", status_code=400)
        old_path = Path(db_norme.fichier_pdf)
        if old_path.exists():
            old_path.unlink()
        file_path = UPLOAD_DIR / fichier_pdf.filename
        with file_path.open("wb") as buffer:
            copyfileobj(fichier_pdf.file, buffer)
        db_norme.fichier_pdf = str(file_path)

    db.commit()
    db.refresh(db_norme)

    return success_response(
        data={
            "id": db_norme.id,
            "codification": db_norme.codification,
            "nom": db_norme.nom,
            "date_creation": db_norme.date_creation.isoformat() if db_norme.date_creation else None,
            "fichier_pdf": db_norme.fichier_pdf,
            "secteur": {"id": db_norme.secteur.id, "nom": db_norme.secteur.nom} if db_norme.secteur else None
        },
        message="Norme mise à jour avec succès"
    )