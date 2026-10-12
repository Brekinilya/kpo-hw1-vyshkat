import math

from vyshkat.domain.errors import DomainError


def require_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainError("Наименование не может быть пустым")
    return value.strip()


def require_positive_int(value: int, field: str) -> int:
    if not _is_int(value) or value <= 0:
        raise DomainError(f"{field}: ожидается целое положительное число")
    return value


def require_int_in_range(value: int, field: str, low: int, high: int) -> int:
    if not _is_int(value) or not low <= value <= high:
        raise DomainError(f"{field}: ожидается целое число от {low} до {high}")
    return value


def require_non_negative_number(value: float, field: str) -> float:
    if not _is_number(value) or not math.isfinite(value) or value < 0:
        raise DomainError(f"{field}: ожидается неотрицательное число")
    return float(value)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)
