class DomainError(Exception):
    """Error base del dominio."""


class InvalidCredentials(DomainError):
    pass


class InvalidToken(DomainError):
    pass


class InvalidSecondFactor(DomainError):
    pass


class InvalidMfaState(DomainError):
    pass


class ReplayAttackDetected(DomainError):
    pass


class UnknownMfaMethod(DomainError):
    pass


class UserAlreadyExists(DomainError):
    pass


class UserNotFound(DomainError):
    pass


class MfaRequired(DomainError):
    pass
