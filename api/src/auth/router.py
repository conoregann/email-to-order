from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from src.auth.service import COOKIE, SESSION_SECONDS, find_guest, new_guest, require_browser_header
from src.config import settings
from src.database import get_db

router = APIRouter(prefix="/auth", tags=["guest"], dependencies=[Depends(require_browser_header)])

@router.post("/guest")
def start_guest(request: Request, response: Response, db: Session = Depends(get_db)):
    guest = find_guest(request, db)
    if guest is None:
        guest, token = new_guest(db)
        response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
                            secure=settings.cookie_secure, samesite="strict", path="/api")
    response.headers["Cache-Control"] = "no-store"
    return {"expires_at": guest.expires_at}
