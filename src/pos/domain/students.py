from dataclasses import dataclass, field

from pos.domain.errors import DomainError
from pos.domain.evaluations import Evaluation, EvaluationFactory
from pos.domain.rubric import Rubric
from pos.domain.values import Score, require_text


@dataclass(frozen=True, eq=False)
class Student:
    identifier: str
    name: str
    _evaluations: dict[str, Evaluation] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        require_text(self.identifier, "Идентификатор студента")
        require_text(self.name, "Имя студента")

    @property
    def evaluations(self) -> tuple[Evaluation, ...]:
        return tuple(self._evaluations.values())

    def assign_evaluation(
        self, rubric: Rubric, criterion_identifier: str, score: Score, comment: str = ""
    ) -> None:
        if criterion_identifier in self._evaluations:
            raise DomainError("Оценка уже выставлена. Используйте исправление оценки.")
        evaluation = EvaluationFactory.create(rubric, criterion_identifier, score, comment)
        self._evaluations[criterion_identifier] = evaluation

    def correct_evaluation(
        self, rubric: Rubric, criterion_identifier: str, score: Score, comment: str = ""
    ) -> None:
        self._require_evaluation(criterion_identifier)
        evaluation = EvaluationFactory.create(rubric, criterion_identifier, score, comment)
        self._evaluations[criterion_identifier] = evaluation

    def cancel_evaluation(self, criterion_identifier: str) -> None:
        self._require_evaluation(criterion_identifier)
        del self._evaluations[criterion_identifier]

    def _require_evaluation(self, criterion_identifier: str) -> None:
        if criterion_identifier not in self._evaluations:
            raise DomainError(f"Оценка по критерию «{criterion_identifier}» ещё не выставлена.")
