import csv
from decimal import Decimal
from pathlib import Path

import pytest

from pos.adapters.csv_export import CsvReportExporter
from pos.application.errors import ApplicationError
from pos.application.facade import GradingFacade
from pos.application.ports import ReportExporter
from pos.application.reports import ScoreMode, ScoreReport
from pos.bootstrap import build_application, build_container


def test_complete_workflow_and_csv_export(tmp_path: Path) -> None:
    application = build_application()
    application.add_student("s1", 'Анна; "Иванова"')
    application.add_student("s2", "Иван")
    application.add_criterion("exam", "Экзамен", Decimal(20), Decimal(1))
    application.assign_evaluation("s1", "exam", Decimal(15))
    application.correct_evaluation("s1", "exam", Decimal(16))
    destination = tmp_path / "итоги.csv"
    assert application.export_report(destination) == 2
    with destination.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter=";"))
    assert rows[0]["Студент"] == 'Анна; "Иванова"'
    assert rows[0]["Результат"] == "8.00"
    assert rows[1]["Результат"] == "не рассчитан"
    assert rows[1]["Оценено"] == "0"
    application.cancel_evaluation("s1", "exam")
    assert application.build_report().rows[0].score is None
    assert application.build_report(ScoreMode.PRELIMINARY).rows[0].score == 0


def test_unknown_student_and_duplicate_identifier_are_rejected() -> None:
    application = build_application()
    application.add_student("s1", "Анна")
    with pytest.raises(ApplicationError):
        application.add_student("s1", "Иван")
    with pytest.raises(ApplicationError):
        application.assign_evaluation("unknown", "exam", Decimal(1))
    assert application.list_students()[0].name == "Анна"


class RecordingExporter:
    def __init__(self) -> None:
        self.reports: list[ScoreReport] = []

    def export(self, report: ScoreReport, destination: Path) -> None:
        self.reports.append(report)


def test_container_shares_repositories_and_allows_exporter_replacement(tmp_path: Path) -> None:
    container = build_container()
    first = container.resolve(GradingFacade)
    first.add_student("s1", "Анна")
    first.add_criterion("exam", "Экзамен", Decimal(10), Decimal(1))
    first.assign_evaluation("s1", "exam", Decimal(9))
    exporter = RecordingExporter()
    container.register(ReportExporter, instance=exporter)
    second = container.resolve(GradingFacade)
    destination = tmp_path / "unused.csv"
    second.export_report(destination)
    assert exporter.reports[0].rows[0].score == 9
    assert not destination.exists()
    assert build_application().list_students() == ()


def test_failed_export_does_not_replace_existing_destination(tmp_path: Path) -> None:
    destination = tmp_path / "directory.csv"
    destination.mkdir()
    marker = destination / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    with pytest.raises(OSError):
        CsvReportExporter().export(ScoreReport(ScoreMode.FINAL, ()), destination)
    assert marker.read_text(encoding="utf-8") == "keep"
    assert list(tmp_path.iterdir()) == [destination]
