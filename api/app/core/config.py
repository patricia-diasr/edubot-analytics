from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configurações da aplicação, lidas de variáveis de ambiente (.env)
    """

    APP_NAME: str = "EduBot Analytics API"
    SECRET_KEY: str = "changeme-super-secret-key-dev-only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
