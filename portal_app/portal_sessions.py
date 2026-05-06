import time
from threading import RLock

from .portal_config import SESSION_TTL_SECONDS
from .portal_security import create_session_token


class SessionStore:
    def __init__(self) -> None:
        self._admin_tokens = {}
        self._student_tokens = {}
        self._lock = RLock()

    def _now(self) -> float:
        return time.time()

    def _prune(self) -> None:
        now = self._now()
        self._admin_tokens = {t: exp for t, exp in self._admin_tokens.items() if exp > now}
        self._student_tokens = {
            roll: (token, exp)
            for roll, (token, exp) in self._student_tokens.items()
            if exp > now
        }

    def create_admin_session(self) -> str:
        with self._lock:
            self._prune()
            token = create_session_token()
            self._admin_tokens[token] = self._now() + SESSION_TTL_SECONDS
            return token

    def is_admin_authenticated(self, token: str) -> bool:
        with self._lock:
            self._prune()
            return bool(token) and token in self._admin_tokens

    def create_student_session(self, roll: str) -> str:
        with self._lock:
            self._prune()
            token = create_session_token()
            self._student_tokens[str(roll)] = (token, self._now() + SESSION_TTL_SECONDS)
            return token

    def is_student_authenticated(self, roll: str, token: str) -> bool:
        with self._lock:
            self._prune()
            current = self._student_tokens.get(str(roll))
            return bool(current and token and current[0] == token)

    def end_student_session(self, roll: str) -> None:
        with self._lock:
            self._student_tokens.pop(str(roll), None)
