from fastapi import APIRouter
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verificar se a API está no ar",
)
def health_check():
    """
    Endpoint público de verificação de saúde da API. Não requer autenticação e não
    consulta o banco, para responder rápido mesmo se outra parte do sistema falhar
    (usado por monitoramento e pelo health check da plataforma de hospedagem)
    """

    return {"status": "ok"}
