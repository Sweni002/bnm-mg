from fastapi import FastAPI, Request
from app.config import Base, engine
from app.api import (
    users_router,
    admins_router,
    clients_router,
    secteurs_router,
    normes_router,
    login_router
)
from app.utils.response import success_response, error_response
from app.utils.auth import decode_access_token

# Création des tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gestion des Normes à Madagascar")

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Routes exemptées du token
    exempt_paths = ["/auth/login", "/admins"]  # ajouter toutes les routes à exempter
    if any(request.url.path.startswith(path) for path in exempt_paths):
        return await call_next(request)

    token = request.headers.get("Authorization")
    if not token:
        return error_response(
            message="Vous devez être connecté pour accéder à cette ressource.",
            status_code=401
        )
    
    token = token.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        return error_response(
            message="Votre session a expiré, veuillez vous reconnecter.",
            status_code=401
        )

    response = await call_next(request)
    return response
# Inclure les routes
app.include_router(users_router)
app.include_router(admins_router)
app.include_router(clients_router)
app.include_router(secteurs_router)
app.include_router(normes_router)
app.include_router(login_router)
