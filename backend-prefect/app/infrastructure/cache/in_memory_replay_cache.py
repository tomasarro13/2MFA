import threading
import time

from ...application.ports import ReplayCache
from ...domain.exceptions import ReplayAttackDetected


class InMemoryReplayCache(ReplayCache):
    """Diccionario (user_id, code) -> instante de uso, con expiración."""

    def __init__(self, ttl_seconds: int):
        self._ttl = ttl_seconds
        self._used: dict[tuple[str, str], float] = {}
        self._lock = threading.Lock()

    def _purge(self, now: float) -> None:
        for key in [k for k, t in self._used.items() if now - t > self._ttl]:
            del self._used[key]

    def was_used(self, user_id: str, code: str) -> bool:
        with self._lock:
            self._purge(time.time())
            return (user_id, code) in self._used

    def mark_used(self, user_id: str, code: str) -> None:
        with self._lock:
            now = time.time()
            self._purge(now)
            if (user_id, code) in self._used:
                raise ReplayAttackDetected(f"El código {code} ya fue utilizado")
            self._used[(user_id, code)] = now
