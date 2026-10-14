import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.docs import DESCRICAO_API, TAGS
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.seed import seed_users
from app.routers import auth, health, predict, solicitacoes

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_users()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=DESCRICAO_API,
    version="0.3.0",
    openapi_tags=TAGS,
    contact={
        "name": "Patricia Dias Rodrigues e Maitê Silva",
        "url": "https://github.com/patricia-diasr/edubot-analytics",
    },
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Devolve o 422 sem ecoar os valores enviados. O handler padrão inclui o campo "input"
    com o que o cliente mandou, o que reflete dados de volta na resposta
    """

    erros = [
        {"type": e["type"], "loc": e["loc"], "msg": e["msg"]} for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": erros}
    )


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(solicitacoes.router)
