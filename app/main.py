from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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
from fastapi.responses import JSONResponse

# Création des tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gestion des Normes à Madagascar")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
      "http://127.0.0.1:5174",   # ← ajouté
    "http://192.168.10.31:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    exempt_paths = ["/auth/login", "/auth/login_client", "/admins", "/ping", "/docs", "/clients"]
# autoriser toutes les routes clients (POST, GET, PUT, DELETE)

    # ✅ Autoriser les preflight et les routes exemptées
    if request.method == "OPTIONS" or any(request.url.path.startswith(path) for path in exempt_paths):
     response = await call_next(request)
     return response

    # Vérification du token pour les autres routes
    token = request.headers.get("Authorization")
    if not token:
        return JSONResponse(
            content={"message": "Vous devez être connecté pour accéder à cette ressource."},
            status_code=401
        )

    token = token.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        return JSONResponse(
            content={"message": "Votre session a expiré, veuillez vous reconnecter."},
            status_code=401
        )

    return await call_next(request)

app.include_router(users_router)
app.include_router(admins_router)
app.include_router(clients_router)
app.include_router(secteurs_router)
app.include_router(normes_router)
app.include_router(login_router)


@app.get("/ping")
async def ping():
    return {"status": "ok"}
