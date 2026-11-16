from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Protocol

from pos.domain.errors import DomainError, IncompleteAssessmentError
from pos.domain.rubric import Rubric
from pos.domain.students import Student


class MissingEvaluationPolicy(Protocol):
    def check(self, missing_criteria: tuple[str, ...]) -> None: ...


class FinalScorePolicy:
    def check(self, missing_criteria: tuple[str, ...]) -> None:
        if missing_criteria:
            raise IncompleteAssessmentError(missing_criteria)


class PreliminaryScorePolicy:
    def check(self, missing_criteria: tuple[str, ...]) -> None:
        pass


@dataclass(frozen=True)
class ScoreResult:
    value: Decimal
    evaluated_criteria: int
    total_criteria: int


class FinalScoreCalculator:
    def calculate(
        self, student: Student, rubric: Rubric, policy: MissingEvaluationPolicy
    ) -> ScoreResult:
        if not rubric.criteria:
            raise DomainError("Нельзя рассчитать результат: рубрикатор пуст.")
        evaluations = {
            evaluation.criterion_identifier: evaluation for evaluation in student.evaluations
        }
        for evaluation in evaluations.values():
            criterion = rubric.get_criterion(evaluation.criterion_identifier)
            if evaluation.score.value > criterion.maximum_score.value:
                raise DomainError("Оценки студента не соответствуют текущему рубрикатору.")
        missing = tuple(
            criterion.identifier
            for criterion in rubric.criteria
            if criterion.identifier not in evaluations
        )
        policy.check(missing)
        with localcontext() as context:
            context.prec = 50
            total_weight = sum(
                (criterion.weight.value for criterion in rubric.criteria), Decimal(0)
            )
            weighted_score = sum(
                (
                    evaluations[criterion.identifier].score.value
                    / criterion.maximum_score.value
                    * (criterion.weight.value / total_weight)
                    for criterion in rubric.criteria
                    if criterion.identifier in evaluations
                ),
                Decimal(0),
            )
            value = min(Decimal(10), max(Decimal(0), Decimal(10) * weighted_score))
        return ScoreResult(value, len(evaluations), len(rubric.criteria))
