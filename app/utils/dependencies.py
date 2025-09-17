from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from app.utils.auth import decode_access_token
from app.utils.response import error_response

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_admin(request: Request, token: str = Depends(oauth2_scheme)):
    # Autoriser la route login sans token
    if request.url.path == "/auth/login":
        return None

    if not token:
        raise HTTPException(status_code=401, detail="Token manquant")

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    return payload  # ici tu peux retourner username ou autre info
