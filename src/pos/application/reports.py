from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class ScoreMode(StrEnum):
    FINAL = "final"
    PRELIMINARY = "preliminary"


@dataclass(frozen=True)
class ReportRow:
    student_identifier: str
    student_name: str
    score: Decimal | None
    evaluated_criteria: int
    total_criteria: int


@dataclass(frozen=True)
class ScoreReport:
    mode: ScoreMode
    rows: tuple[ReportRow, ...]
