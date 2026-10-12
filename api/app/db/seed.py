import logging
from sqlmodel import Session, select
from app.core.config import settings
from app.core.database import engine
from app.core.hashing import get_password_hash
from app.models.db_models import Solicitacao, User

logger = logging.getLogger("edubot.seed")

# Usuários e solicitações de teste, para validar os fluxos e servir de alvo no pentest.
# As senhas vêm de variáveis de ambiente, nunca do código
_SEED_USERS = [
    {
        "username": "aluno.teste",
        "full_name": "Aluno de Teste",
        "password_env": "SEED_PASSWORD_ALUNO1",
        "solicitacoes": [
            "Preciso trancar a disciplina de Cálculo II, o prazo termina amanhã",
            "Gostaria de consultar minha nota final de Estatística",
        ],
    },
    {
        "username": "aluno.teste2",
        "full_name": "Segundo Aluno de Teste",
        "password_env": "SEED_PASSWORD_ALUNO2",
        "solicitacoes": [
            "Não consigo acessar o portal do aluno para fazer a matrícula",
            "Quero pedir revisão da prova de Física I",
        ],
    },
    {
        "username": "aluno.teste3",
        "full_name": "Terceiro Aluno de Teste",
        "password_env": "SEED_PASSWORD_ALUNO3",
        "solicitacoes": [
            "Como faço para emitir o boleto da rematrícula?",
        ],
    },
]


def seed_users() -> None:
    with Session(engine) as session:
        for data in _SEED_USERS:
            password = getattr(settings, data["password_env"])
            if not password:
                logger.warning(
                    "%s não definida, usuário %s não foi criado",
                    data["password_env"],
                    data["username"],
                )
                continue

            existing = session.exec(
                select(User).where(User.username == data["username"])
            ).first()

            if existing:
                continue

            user = User(
                username=data["username"],
                full_name=data["full_name"],
                hashed_password=get_password_hash(password),
            )
            session.add(user)
            session.flush()

            for mensagem in data["solicitacoes"]:
                session.add(Solicitacao(mensagem=mensagem, usuario_id=user.id))

        session.commit()
