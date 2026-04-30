import secrets
import string

from .portal_config import PASSWORD_LENGTH


def generate_password(length: int = PASSWORD_LENGTH) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_session_token(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
