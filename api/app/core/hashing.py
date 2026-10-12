import bcrypt

# O bcrypt só considera os primeiros 72 bytes da senha, e a versão 5 da biblioteca
# lança erro acima disso. Senhas maiores são simplesmente recusadas no login
_BCRYPT_MAX_BYTES = 72

# Hash fixo usado quando o usuário não existe. Fazer a verificação mesmo assim deixa o
# tempo de resposta igual nos dois casos e impede descobrir usuários válidos pelo tempo
_DUMMY_HASH = bcrypt.hashpw(b"usuario-inexistente", bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    senha = plain_password.encode("utf-8")
    if len(senha) > _BCRYPT_MAX_BYTES:
        return False
    return bcrypt.checkpw(senha, hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    senha = password.encode("utf-8")
    if len(senha) > _BCRYPT_MAX_BYTES:
        raise ValueError(f"Senha maior que {_BCRYPT_MAX_BYTES} bytes")
    return bcrypt.hashpw(senha, bcrypt.gensalt()).decode("utf-8")


def simulate_password_check() -> None:
    """Gasta o mesmo tempo de uma verificação real, para usuários inexistentes"""

    bcrypt.checkpw(b"senha-qualquer", _DUMMY_HASH.encode("utf-8"))
