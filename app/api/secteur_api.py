from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.secteur import Secteur
from app.config.database import SessionLocal
from app.schemas import SecteurCreate
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/secteurs", tags=["Secteurs"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_secteur(secteur: SecteurCreate, db: Session = Depends(get_db)):
    try:
        # Vérification du champ obligatoire
        if not secteur.nom or not secteur.nom.strip():
            return error_response(message="Le champ 'nom' est obligatoire", status_code=400)

        # Vérifier si le secteur existe déjà
        existing = db.query(Secteur).filter(Secteur.nom == secteur.nom.strip()).first()
        if existing:
            return error_response(message="Ce secteur existe déjà", status_code=400)

        # Créer le secteur
        db_secteur = Secteur(nom=secteur.nom.strip())
        db.add(db_secteur)
        db.commit()
        db.refresh(db_secteur)

        return success_response(
            data={"id": db_secteur.id, "nom": db_secteur.nom},
            message="Secteur créé avec succès"
        )

    except Exception as e:
        return error_response(message=str(e))

# ----------------- Lire tous les Secteurs -----------------
@router.get("/")
def read_secteurs(db: Session = Depends(get_db)):
    secteurs = db.query(Secteur).all()
    data = [{"id": s.id, "nom": s.nom} for s in secteurs]
    return success_response(data=data)


# ----------------- Lire un Secteur -----------------
@router.get("/{secteur_id}")
def read_secteur(secteur_id: int, db: Session = Depends(get_db)):
    db_secteur = db.query(Secteur).filter(Secteur.id == secteur_id).first()
    if not db_secteur:
        return error_response(message="Secteur non trouvé", status_code=404)
    return success_response(data={"id": db_secteur.id, "nom": db_secteur.nom})


# ----------------- Supprimer un Secteur -----------------
@router.delete("/{secteur_id}")
def delete_secteur(secteur_id: int, db: Session = Depends(get_db)):
    db_secteur = db.query(Secteur).filter(Secteur.id == secteur_id).first()
    if not db_secteur:
        return error_response(message="Secteur non trouvé", status_code=404)

    # Vérifier s’il a des normes associées
    if db_secteur.normes and len(db_secteur.normes) > 0:
        return error_response(message="Impossible de supprimer un secteur qui contient des normes", status_code=400)

    db.delete(db_secteur)
    db.commit()
    return success_response(
        data={"id": db_secteur.id, "nom": db_secteur.nom},
        message="Secteur supprimé avec succès"
    )



@router.put("/{secteur_id}")
def update_secteur(secteur_id: int, secteur: SecteurCreate, db: Session = Depends(get_db)):
    try:
        # Vérifier que le champ nom n'est pas vide
        if not secteur.nom or not secteur.nom.strip():
            return error_response(message="Le champ 'nom' est obligatoire", status_code=400)

        db_secteur = db.query(Secteur).filter(Secteur.id == secteur_id).first()
        if not db_secteur:
            return error_response(message="Secteur non trouvé", status_code=404)

        # Vérifier l'unicité du nom pour les autres secteurs
        existing = db.query(Secteur).filter(
            Secteur.nom == secteur.nom.strip(),
            Secteur.id != secteur_id
        ).first()
        if existing:
            return error_response(message="Ce nom de secteur existe déjà", status_code=400)

        # Mettre à jour
        db_secteur.nom = secteur.nom.strip()
        db.commit()
        db.refresh(db_secteur)

        return success_response(
            data={"id": db_secteur.id, "nom": db_secteur.nom},
            message="Secteur mis à jour avec succès"
        )

    except Exception as e:
        return error_response(message=str(e))
