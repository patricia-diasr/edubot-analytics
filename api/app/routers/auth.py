import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.core.config import settings
from app.core.database import get_session
from app.core.docs import RESPOSTA_422, resposta_429
from app.core.rate_limit import get_client_ip, limiter
from app.core.security import authenticate_user, create_access_token
from app.models.schemas import ErroSimples, Token

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("edubot.security")


@router.post(
    "/token",
    response_model=Token,
    summary="Fazer login e obter o token JWT",
    responses={
        401: {
            "model": ErroSimples,
            "description": "Usuário ou senha incorretos. A resposta é a mesma para "
            "usuário inexistente, para não revelar quais usuários existem",
            "content": {
                "application/json": {
                    "example": {"detail": "Usuário ou senha incorretos"}
                }
            },
        },
        **RESPOSTA_422,
        **resposta_429(settings.RATE_LIMIT_LOGIN),
    },
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """
    Login no padrão OAuth2 *password flow*: envie `username` e `password` como
    formulário (`application/x-www-form-urlencoded`). Retorna um JWT válido por
    30 minutos, que deve ser enviado no header `Authorization: Bearer <token>`.

    Limitado a **5 tentativas por minuto por IP**, contra força bruta. Tentativas que
    falham são registradas em log (usuário e IP, nunca a senha)
    """

    user = authenticate_user(session, form_data.username, form_data.password)

    if not user:
        # Registra a tentativa para auditoria, sem nunca gravar a senha
        # Os headers de IP recebidos ficam no log para investigação (ex: tentativa de
        # falsificar o IP para escapar do rate limit)
        logger.warning(
            "login_falhou usuario=%r ip=%s x_forwarded_for=%r cf_connecting_ip=%r",
            form_data.username,
            get_client_ip(request),
            request.headers.get("x-forwarded-for"),
            request.headers.get("cf-connecting-ip"),
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
