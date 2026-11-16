from pathlib import Path
from typing import Protocol

from pos.application.reports import ScoreReport
from pos.domain.rubric import Rubric
from pos.domain.students import Student


class StudentRepository(Protocol):
    def add(self, student: Student) -> None: ...

    def get(self, identifier: str) -> Student: ...

    def list_students(self) -> tuple[Student, ...]: ...

    def save(self, student: Student) -> None: ...


class RubricRepository(Protocol):
    def get(self) -> Rubric: ...

    def save(self, rubric: Rubric) -> None: ...


class ReportExporter(Protocol):
    def export(self, report: ScoreReport, destination: Path) -> None: ...
