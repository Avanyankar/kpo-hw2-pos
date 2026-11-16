from dataclasses import dataclass

from pos.domain.errors import DomainError
from pos.domain.rubric import Rubric
from pos.domain.values import Score, require_text


@dataclass(frozen=True)
class Evaluation:
    criterion_identifier: str
    score: Score
    comment: str = ""

    def __post_init__(self) -> None:
        require_text(self.criterion_identifier, "Идентификатор критерия")


class EvaluationFactory:
    @staticmethod
    def create(
        rubric: Rubric, criterion_identifier: str, score: Score, comment: str = ""
    ) -> Evaluation:
        criterion = rubric.get_criterion(criterion_identifier)
        if score.value > criterion.maximum_score.value:
            raise DomainError(
                f"Балл по критерию «{criterion.name}» должен быть от 0 "
                f"до {criterion.maximum_score.value}."
            )
        return Evaluation(criterion_identifier, score, comment)
