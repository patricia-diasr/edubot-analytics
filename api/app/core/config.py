from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valores que já apareceram em código/documentação pública e por isso nunca podem ser
# usados como chave de assinatura do JWT
_CHAVES_PROIBIDAS = {
    "changeme-super-secret-key-dev-only",
    "coloque-aqui-uma-chave-secreta-forte",
}
_TAMANHO_MINIMO_CHAVE = 32


class Settings(BaseSettings):
    """
    Configurações da aplicação, lidas de variáveis de ambiente (.env)
    """

    # hide_input_in_errors evita que o valor da chave apareça nos logs se ela for recusada
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", hide_input_in_errors=True
    )

    APP_NAME: str = "EduBot Analytics API"

    # Sem valor padrão de propósito: a API não sobe sem uma chave definida no ambiente.
    # No TP2 havia um default fixo no código, o que permitia forjar tokens se o .env faltasse
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "sqlite:///./edubot.db"

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Rate limiting (ver justificativa em security/decisoes-tecnicas.md)
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_PREDICT: str = "20/minute"
    # Quantidade de proxies confiáveis na frente da API (0 = acesso direto, sem proxy).
    # Atrás de um proxy, o IP de quem conecta é sempre o do proxy, então o IP real do
    # cliente precisa ser lido do header X-Forwarded-For
    TRUSTED_PROXY_HOPS: int = 0
    # Header com o IP real do cliente, preenchido por um proxy confiável que sobrescreve
    # qualquer valor enviado pelo cliente. No Render, a Cloudflare fica na frente e envia
    # o IP em "cf-connecting-ip". Quando definido, tem prioridade sobre TRUSTED_PROXY_HOPS
    CLIENT_IP_HEADER: Optional[str] = None

    # Senhas dos usuários de teste criados na inicialização. Usuário sem senha definida
    # não é criado
    SEED_PASSWORD_ALUNO1: Optional[str] = None
    SEED_PASSWORD_ALUNO2: Optional[str] = None
    SEED_PASSWORD_ALUNO3: Optional[str] = None

    @field_validator("SECRET_KEY")
    @classmethod
    def validar_secret_key(cls, value: str) -> str:
        if value in _CHAVES_PROIBIDAS:
            raise ValueError(
                "SECRET_KEY usa um valor de exemplo público, gere uma chave própria"
            )
        if len(value) < _TAMANHO_MINIMO_CHAVE:
            raise ValueError(
                f"SECRET_KEY precisa ter pelo menos {_TAMANHO_MINIMO_CHAVE} caracteres"
            )
        return value


settings = Settings()
