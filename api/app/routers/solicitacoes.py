from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlmodel import Session
from app.core.database import get_session
from app.core.docs import RESPOSTA_401, RESPOSTA_422
from app.core.security import get_current_user
from app.models.db_models import Solicitacao, User
from app.models.schemas import ErroSimples, SolicitacaoRead

router = APIRouter(prefix="/solicitacoes", tags=["solicitacoes"])

RESPOSTA_404 = {
    404: {
        "model": ErroSimples,
        "description": "Solicitação inexistente **ou** pertencente a outro aluno. As "
        "duas situações têm a mesma resposta para não revelar quais IDs existem",
        "content": {
            "application/json": {"example": {"detail": "Solicitação não encontrada"}}
        },
    }
}


@router.get(
    "/{solicitacao_id}",
    response_model=SolicitacaoRead,
    summary="Consultar uma solicitação do próprio aluno",
    responses={**RESPOSTA_401, **RESPOSTA_404, **RESPOSTA_422},
)
def get_solicitacao(
    solicitacao_id: int = Path(
        ge=1, description="ID retornado pelo `POST /predict`", examples=[1]
    ),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Retorna uma solicitação pelo ID, **apenas se ela pertencer ao aluno autenticado**
    (proteção contra BOLA/IDOR). O dono é identificado pelo token JWT, nunca por um
    parâmetro da requisição
    """
    solicitacao = session.get(Solicitacao, solicitacao_id)
    if solicitacao is None or solicitacao.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação não encontrada",
        )
    return solicitacao
