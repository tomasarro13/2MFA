from collections.abc import Iterable

from ..domain.exceptions import UnknownMfaMethod
from ..domain.strategies import SecondFactorStrategy


class StrategyRegistry:
    """Open/Closed: agregar un nuevo segundo factor = registrar otra estrategia."""

    def __init__(self, strategies: Iterable[SecondFactorStrategy]):
        self._strategies = {s.name: s for s in strategies}

    def get(self, name: str) -> SecondFactorStrategy:
        try:
            return self._strategies[name]
        except KeyError:
            raise UnknownMfaMethod(f"Método 2FA desconocido: '{name}'. Opciones: {sorted(self._strategies)}")
