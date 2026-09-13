from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações da aplicação, lidas de variáveis de ambiente (.env)
    """

    model_config = SettingsConfigDict(env_file=".env")

    APP_NAME: str = "EduBot Analytics API"
    SECRET_KEY: str = "changeme-super-secret-key-dev-only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
