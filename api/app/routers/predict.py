from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.models.schemas import PredictRequest, PredictResponse, UserInDB

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictResponse)
def predict(
    payload: PredictRequest, current_user: UserInDB = Depends(get_current_user)
):
    """
    Rota protegida por JWT (retorna 401 sem token válido)
    """

    return PredictResponse(
        categoria="placeholder", urgencia="placeholder", status="not_implemented"
    )
