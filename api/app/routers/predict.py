from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from app.core.config import settings
from app.core.database import get_session
from app.core.docs import RESPOSTA_401, RESPOSTA_422, resposta_429
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.models.db_models import Solicitacao, User
from app.models.schemas import SolicitacaoCreate, SolicitacaoRead

router = APIRouter(tags=["predict"])


@router.post(
    "/predict",
    response_model=SolicitacaoRead,
    summary="Enviar um pedido do aluno para classificação",
    responses={
        **RESPOSTA_401,
        **RESPOSTA_422,
        **resposta_429(settings.RATE_LIMIT_PREDICT),
    },
)
@limiter.limit(settings.RATE_LIMIT_PREDICT)
def predict(
    request: Request,
    payload: SolicitacaoCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Recebe a mensagem do aluno e cria uma solicitação vinculada ao aluno autenticado
    (o dono vem do token JWT, não do corpo da requisição).

    Por enquanto `categoria` e `urgencia` retornam `placeholder`: o modelo de
    classificação e o agente serão integrados no TP4. O `id` retornado pode ser
    consultado em `GET /solicitacoes/{id}`
    """

    solicitacao = Solicitacao(
        mensagem=payload.mensagem,
        usuario_id=current_user.id,
    )
    session.add(solicitacao)
    session.commit()
    session.refresh(solicitacao)
    return solicitacao
