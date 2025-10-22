
class CoordinationError(Exception):
    """Базовое исключение для всех ошибок координации."""


class NodeAlreadyExists(CoordinationError):
    """Узел координации уже существует."""


class NodeNotFound(CoordinationError):
    """Узел координации не найден."""


class NodeLocked(CoordinationError):
    """Узел координации уже захвачен."""


class NodeTimeout(CoordinationError):
    """Истекло время ожидания при захвате узла."""