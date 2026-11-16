from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from pos.domain.errors import DomainError, IncompleteAssessmentError
from pos.domain.evaluations import EvaluationFactory
from pos.domain.rubric import Criterion, Rubric
from pos.domain.scoring import FinalScoreCalculator, FinalScorePolicy, PreliminaryScorePolicy
from pos.domain.students import Student
from pos.domain.values import Score, Weight


@pytest.fixture
def rubric() -> Rubric:
    result = Rubric()
    result.add_criterion(Criterion("homework", "Задания", Score(Decimal(10)), Weight(Decimal(40))))
    result.add_criterion(Criterion("exam", "Экзамен", Score(Decimal(20)), Weight(Decimal(60))))
    return result


@pytest.mark.parametrize("value", ["-0.01", "NaN", "sNaN", "Infinity", "-Infinity"])
def test_invalid_score_is_rejected(value: str) -> None:
    with pytest.raises(DomainError):
        Score(Decimal(value))


@pytest.mark.parametrize("value", ["0", "-1", "NaN", "Infinity"])
def test_invalid_weight_is_rejected(value: str) -> None:
    with pytest.raises(DomainError):
        Weight(Decimal(value))


def test_zero_maximum_is_rejected() -> None:
    with pytest.raises(DomainError):
        Criterion("exam", "Экзамен", Score(Decimal(0)), Weight(Decimal(1)))


@pytest.mark.parametrize("value", ["0", "10", "7.25"])
def test_factory_accepts_boundaries_and_fractional_scores(rubric: Rubric, value: str) -> None:
    evaluation = EvaluationFactory.create(rubric, "homework", Score(Decimal(value)))
    assert evaluation.score == Score(Decimal(value))


def test_unknown_criterion_and_excess_score_cannot_enter_student(rubric: Rubric) -> None:
    student = Student("s1", "Анна")
    for identifier, value in [("unknown", "5"), ("homework", "10.01")]:
        with pytest.raises(DomainError):
            student.assign_evaluation(rubric, identifier, Score(Decimal(value)))
    assert student.evaluations == ()


def test_duplicate_evaluation_requires_explicit_correction(rubric: Rubric) -> None:
    student = Student("s1", "Анна")
    student.assign_evaluation(rubric, "homework", Score(Decimal(8)), "Исходная оценка")
    with pytest.raises(DomainError):
        student.assign_evaluation(rubric, "homework", Score(Decimal(10)))
    with pytest.raises(DomainError):
        student.correct_evaluation(rubric, "homework", Score(Decimal(11)))
    assert student.evaluations[0].score.value == 8
    assert student.evaluations[0].comment == "Исходная оценка"


def test_correction_replaces_value_and_cancellation_removes_it(rubric: Rubric) -> None:
    student = Student("s1", "Анна")
    student.assign_evaluation(rubric, "homework", Score(Decimal(8)))
    original = student.evaluations[0]
    student.correct_evaluation(rubric, "homework", Score(Decimal(9)), "Исправлено")
    assert original.score.value == 8
    assert student.evaluations[0].score.value == 9
    assert student.evaluations[0].comment == "Исправлено"
    student.cancel_evaluation("homework")
    assert student.evaluations == ()
    with pytest.raises(DomainError):
        student.cancel_evaluation("homework")
    with pytest.raises(DomainError):
        student.correct_evaluation(rubric, "homework", Score(Decimal(8)))


def test_rubric_rejects_duplicate_and_criterion_cannot_be_mutated(rubric: Rubric) -> None:
    criterion = rubric.get_criterion("exam")
    with pytest.raises(DomainError):
        rubric.add_criterion(criterion)
    with pytest.raises(FrozenInstanceError):
        criterion.__setattr__("maximum_score", Score(Decimal(1)))


@pytest.mark.parametrize("identifier,name", [("", "Анна"), ("s1", "  ")])
def test_student_requires_identifier_and_name(identifier: str, name: str) -> None:
    with pytest.raises(DomainError):
        Student(identifier, name)


def test_weighted_result_uses_each_maximum_and_normalizes_weights(rubric: Rubric) -> None:
    student = Student("s1", "Анна")
    student.assign_evaluation(rubric, "homework", Score(Decimal(8)))
    student.assign_evaluation(rubric, "exam", Score(Decimal(15)))
    calculator = FinalScoreCalculator()
    assert calculator.calculate(student, rubric, FinalScorePolicy()).value == Decimal("7.7")
    student.correct_evaluation(rubric, "exam", Score(Decimal(18)))
    assert calculator.calculate(student, rubric, FinalScorePolicy()).value == Decimal("8.6")
    student.cancel_evaluation("exam")
    assert calculator.calculate(student, rubric, PreliminaryScorePolicy()).value == Decimal("3.2")
    with pytest.raises(IncompleteAssessmentError):
        calculator.calculate(student, rubric, FinalScorePolicy())


def test_missing_grade_differs_from_zero(rubric: Rubric) -> None:
    student = Student("s1", "Анна")
    student.assign_evaluation(rubric, "homework", Score(Decimal(0)))
    calculator = FinalScoreCalculator()
    with pytest.raises(IncompleteAssessmentError) as failure:
        calculator.calculate(student, rubric, FinalScorePolicy())
    assert failure.value.missing_criteria == ("exam",)
    result = calculator.calculate(student, rubric, PreliminaryScorePolicy())
    assert result.value == Decimal(0)
    assert (result.evaluated_criteria, result.total_criteria) == (1, 2)
    student.assign_evaluation(rubric, "exam", Score(Decimal(0)))
    assert calculator.calculate(student, rubric, FinalScorePolicy()).value == 0


def test_adding_criterion_invalidates_previous_complete_result(rubric: Rubric) -> None:
    student = Student("s1", "Анна")
    student.assign_evaluation(rubric, "homework", Score(Decimal(10)))
    student.assign_evaluation(rubric, "exam", Score(Decimal(20)))
    calculator = FinalScoreCalculator()
    assert calculator.calculate(student, rubric, FinalScorePolicy()).value == 10
    rubric.add_criterion(Criterion("project", "Проект", Score(Decimal(10)), Weight(Decimal(100))))
    with pytest.raises(IncompleteAssessmentError):
        calculator.calculate(student, rubric, FinalScorePolicy())
    assert calculator.calculate(student, rubric, PreliminaryScorePolicy()).value == 5


def test_empty_rubric_has_no_result() -> None:
    with pytest.raises(DomainError):
        FinalScoreCalculator().calculate(Student("s1", "Анна"), Rubric(), PreliminaryScorePolicy())


def test_no_intermediate_rounding() -> None:
    rubric = Rubric()
    rubric.add_criterion(Criterion("exam", "Экзамен", Score(Decimal(3)), Weight(Decimal(1))))
    student = Student("s1", "Анна")
    student.assign_evaluation(rubric, "exam", Score(Decimal(1)))
    result = FinalScoreCalculator().calculate(student, rubric, FinalScorePolicy())
    assert Decimal("3.333333333333") < result.value < Decimal("3.333333333334")
