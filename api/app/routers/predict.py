from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.core.security import get_current_user
from app.models.db_models import Solicitacao, User
from app.models.schemas import SolicitacaoCreate, SolicitacaoRead

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=SolicitacaoRead)
def predict(
    payload: SolicitacaoCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Rota protegida por JWT, persiste a solicitação vinculada ao aluno autenticado
    """

    solicitacao = Solicitacao(
        mensagem=payload.mensagem,
        usuario_id=current_user.id,
    )
    session.add(solicitacao)
    session.commit()
    session.refresh(solicitacao)
    return solicitacao
