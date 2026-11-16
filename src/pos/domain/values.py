from dataclasses import dataclass
from decimal import Decimal

from pos.domain.errors import DomainError


def require_text(value: str, label: str) -> None:
    if not value.strip():
        raise DomainError(f"{label} не может быть пустым.")


@dataclass(frozen=True)
class Score:
    value: Decimal

    def __post_init__(self) -> None:
        if not self.value.is_finite() or self.value < 0:
            raise DomainError("Балл должен быть конечным неотрицательным числом.")


@dataclass(frozen=True)
class Weight:
    value: Decimal

    def __post_init__(self) -> None:
        if not self.value.is_finite() or self.value <= 0:
            raise DomainError("Вес должен быть конечным положительным числом.")
