import csv
from pathlib import Path
from tempfile import NamedTemporaryFile

from pos.adapters.formatting import format_mode, format_score
from pos.application.reports import ScoreReport


class CsvReportExporter:
    def export(self, report: ScoreReport, destination: Path) -> None:
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8-sig",
                newline="",
                dir=destination.parent,
                suffix=".csv",
                delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                writer = csv.writer(stream, delimiter=";")
                writer.writerow(
                    ["Идентификатор", "Студент", "Результат", "Оценено", "Всего", "Режим"]
                )
                for row in report.rows:
                    writer.writerow(
                        [
                            row.student_identifier,
                            row.student_name,
                            format_score(row.score),
                            row.evaluated_criteria,
                            row.total_criteria,
                            format_mode(report.mode),
                        ]
                    )
            temporary_path.replace(destination)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
