from fastapi import FastAPI
from app.core.config import settings
from app.routers import auth, health, predict

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API base do EduBot Analytics - Suporte Acadêmico Universitário. "
        "TP1: estrutura modular do FastAPI + autenticação JWT."
    ),
    version="0.1.0",
)


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
