from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.database import get_session
from app.core.security import get_current_user
from app.models.db_models import Solicitacao, User
from app.models.schemas import SolicitacaoRead

router = APIRouter(prefix="/solicitacoes", tags=["solicitacoes"])


@router.get("/{solicitacao_id}", response_model=SolicitacaoRead)
def get_solicitacao(
    solicitacao_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Retorna uma solicitação pelo ID, apenas se ela pertencer ao usuário autenticado
    """
    solicitacao = session.get(Solicitacao, solicitacao_id)
    if solicitacao is None or solicitacao.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada",
        )
    return solicitacao
