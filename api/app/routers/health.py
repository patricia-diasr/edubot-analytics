from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """
    Endpoint público de verificação de saúde da API. Não requer autenticação (usado por monitoramento / uptime checks)
    """

    return {"status": "ok"}
