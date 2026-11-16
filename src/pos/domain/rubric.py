from dataclasses import dataclass, field

from pos.domain.errors import DomainError
from pos.domain.values import Score, Weight, require_text


@dataclass(frozen=True, eq=False)
class Criterion:
    identifier: str
    name: str
    maximum_score: Score
    weight: Weight

    def __post_init__(self) -> None:
        require_text(self.identifier, "Идентификатор критерия")
        require_text(self.name, "Название критерия")
        if self.maximum_score.value == 0:
            raise DomainError("Максимальный балл должен быть положительным.")


@dataclass(frozen=True, eq=False)
class Rubric:
    _criteria: dict[str, Criterion] = field(default_factory=dict, init=False, repr=False)

    @property
    def criteria(self) -> tuple[Criterion, ...]:
        return tuple(self._criteria.values())

    def add_criterion(self, criterion: Criterion) -> None:
        if criterion.identifier in self._criteria:
            raise DomainError(f"Критерий «{criterion.identifier}» уже существует.")
        self._criteria[criterion.identifier] = criterion

    def get_criterion(self, identifier: str) -> Criterion:
        try:
            return self._criteria[identifier]
        except KeyError as error:
            raise DomainError(f"Критерий «{identifier}» отсутствует в рубрикаторе.") from error
