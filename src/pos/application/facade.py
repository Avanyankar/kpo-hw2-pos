from decimal import Decimal
from pathlib import Path

from pos.application.ports import ReportExporter, RubricRepository, StudentRepository
from pos.application.reports import ReportRow, ScoreMode, ScoreReport
from pos.domain.errors import DomainError, IncompleteAssessmentError
from pos.domain.evaluations import Evaluation
from pos.domain.rubric import Criterion
from pos.domain.scoring import (
    FinalScoreCalculator,
    FinalScorePolicy,
    MissingEvaluationPolicy,
    PreliminaryScorePolicy,
    ScoreResult,
)
from pos.domain.students import Student
from pos.domain.values import Score, Weight


class GradingFacade:
    def __init__(
        self,
        students: StudentRepository,
        rubric: RubricRepository,
        calculator: FinalScoreCalculator,
        exporter: ReportExporter,
        final_policy: FinalScorePolicy,
        preliminary_policy: PreliminaryScorePolicy,
    ) -> None:
        self._students = students
        self._rubric = rubric
        self._calculator = calculator
        self._exporter = exporter
        self._policies: dict[ScoreMode, MissingEvaluationPolicy] = {
            ScoreMode.FINAL: final_policy,
            ScoreMode.PRELIMINARY: preliminary_policy,
        }

    def add_student(self, identifier: str, name: str) -> None:
        self._students.add(Student(identifier, name))

    def list_students(self) -> tuple[Student, ...]:
        return self._students.list_students()

    def add_criterion(
        self, identifier: str, name: str, maximum_score: Decimal, weight: Decimal
    ) -> None:
        criterion = Criterion(identifier, name, Score(maximum_score), Weight(weight))
        rubric = self._rubric.get()
        rubric.add_criterion(criterion)
        self._rubric.save(rubric)

    def list_criteria(self) -> tuple[Criterion, ...]:
        return self._rubric.get().criteria

    def assign_evaluation(
        self, student_identifier: str, criterion_identifier: str, score: Decimal, comment: str = ""
    ) -> None:
        student = self._students.get(student_identifier)
        student.assign_evaluation(self._rubric.get(), criterion_identifier, Score(score), comment)
        self._students.save(student)

    def correct_evaluation(
        self, student_identifier: str, criterion_identifier: str, score: Decimal, comment: str = ""
    ) -> None:
        student = self._students.get(student_identifier)
        student.correct_evaluation(self._rubric.get(), criterion_identifier, Score(score), comment)
        self._students.save(student)

    def cancel_evaluation(self, student_identifier: str, criterion_identifier: str) -> None:
        student = self._students.get(student_identifier)
        student.cancel_evaluation(criterion_identifier)
        self._students.save(student)

    def list_evaluations(self, student_identifier: str) -> tuple[Evaluation, ...]:
        return self._students.get(student_identifier).evaluations

    def calculate_score(
        self, student_identifier: str, mode: ScoreMode = ScoreMode.FINAL
    ) -> ScoreResult:
        return self._calculator.calculate(
            self._students.get(student_identifier), self._rubric.get(), self._policies[mode]
        )

    def build_report(self, mode: ScoreMode = ScoreMode.FINAL) -> ScoreReport:
        rubric = self._rubric.get()
        if not rubric.criteria:
            raise DomainError("Нельзя построить ведомость: рубрикатор пуст.")
        rows = []
        for student in self._students.list_students():
            try:
                result = self._calculator.calculate(student, rubric, self._policies[mode])
                score: Decimal | None = result.value
            except IncompleteAssessmentError:
                score = None
            rows.append(
                ReportRow(
                    student.identifier,
                    student.name,
                    score,
                    len(student.evaluations),
                    len(rubric.criteria),
                )
            )
        return ScoreReport(mode, tuple(rows))

    def export_report(self, destination: Path, mode: ScoreMode = ScoreMode.FINAL) -> int:
        report = self.build_report(mode)
        self._exporter.export(report, destination)
        return len(report.rows)
