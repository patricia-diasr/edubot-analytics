import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.core.config import settings
from app.core.database import get_session
from app.core.rate_limit import get_client_ip, limiter
from app.core.security import authenticate_user, create_access_token
from app.models.schemas import Token

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("edubot.security")


@router.post("/token", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, form_data.username, form_data.password)

    if not user:
        # Registra a tentativa para auditoria, sem nunca gravar a senha
        logger.warning(
            "login_falhou usuario=%r ip=%s", form_data.username, get_client_ip(request)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")
