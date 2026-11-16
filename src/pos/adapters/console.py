import shlex
from collections.abc import Callable
from decimal import Decimal, DecimalException
from pathlib import Path
from typing import TextIO

from pos.adapters.formatting import format_mode, format_score
from pos.application.errors import ApplicationError
from pos.application.facade import GradingFacade
from pos.application.reports import ScoreMode
from pos.domain.errors import DomainError

HELP = """Команды (аргументы с пробелами заключайте в двойные кавычки):
  student add <идентификатор> "<имя>"
  student list
  criterion add <идентификатор> "<название>" <максимум> <вес>
  criterion list
  evaluation set <студент> <критерий> <балл> ["<комментарий>"]
  evaluation change <студент> <критерий> <балл> ["<комментарий>"]
  evaluation remove <студент> <критерий>
  evaluation list <студент>
  total <студент> [final|preliminary]
  report [final|preliminary]
  export "<путь.csv>" [final|preliminary]
  help
  exit
Режим по умолчанию: final. preliminary считает пропущенные оценки нулями.
Дробные числа: через точку. Пути Windows: в кавычках или с прямыми слешами.
Данные хранятся только до завершения программы. export перезаписывает указанный файл."""


class CommandProcessor:
    def __init__(self, application: GradingFacade, output: TextIO) -> None:
        self._application = application
        self._output = output
        self._commands: dict[tuple[str, ...], Callable[[list[str]], None]] = {
            ("student", "add"): self._add_student,
            ("student", "list"): self._list_students,
            ("criterion", "add"): self._add_criterion,
            ("criterion", "list"): self._list_criteria,
            ("evaluation", "set"): self._assign_evaluation,
            ("evaluation", "change"): self._correct_evaluation,
            ("evaluation", "remove"): self._cancel_evaluation,
            ("evaluation", "list"): self._list_evaluations,
            ("total",): self._total,
            ("report",): self._report,
            ("export",): self._export,
            ("help",): self._help,
        }
        self.had_errors = False

    def execute(self, line: str) -> bool:
        try:
            tokens = shlex.split(line, comments=True)
            if not tokens:
                return True
            if tokens[0] == "exit":
                self._require_count(tokens[1:], 0)
                return False
            prefix_length = 2 if tokens[0] in {"student", "criterion", "evaluation"} else 1
            handler = self._commands.get(tuple(tokens[:prefix_length]))
            if handler is None:
                raise ValueError("Неизвестная команда. Введите help для справки.")
            handler(tokens[prefix_length:])
        except (DomainError, ApplicationError, ValueError, DecimalException, OSError) as error:
            self.had_errors = True
            self._write(f"Ошибка: {error}")
        return True

    def _write(self, message: str) -> None:
        print(message, file=self._output)

    @staticmethod
    def _require_count(arguments: list[str], minimum: int, maximum: int | None = None) -> None:
        maximum = minimum if maximum is None else maximum
        if not minimum <= len(arguments) <= maximum:
            raise ValueError("Неверное количество аргументов. Синтаксис команд: help.")

    @staticmethod
    def _number(text: str) -> Decimal:
        try:
            return Decimal(text)
        except DecimalException as error:
            raise ValueError(f"«{text}» — не число. Дробную часть отделяйте точкой.") from error

    @staticmethod
    def _mode(arguments: list[str]) -> ScoreMode:
        try:
            return ScoreMode(arguments[0]) if arguments else ScoreMode.FINAL
        except ValueError as error:
            raise ValueError("Режим должен быть final или preliminary.") from error

    def _add_student(self, arguments: list[str]) -> None:
        self._require_count(arguments, 2)
        self._application.add_student(arguments[0], arguments[1])
        self._write("Студент добавлен.")

    def _list_students(self, arguments: list[str]) -> None:
        self._require_count(arguments, 0)
        students = self._application.list_students()
        for student in students:
            self._write(f"{student.identifier}: {student.name}")
        if not students:
            self._write("Студентов пока нет.")

    def _add_criterion(self, arguments: list[str]) -> None:
        self._require_count(arguments, 4)
        self._application.add_criterion(
            arguments[0], arguments[1], self._number(arguments[2]), self._number(arguments[3])
        )
        self._write("Критерий добавлен.")

    def _list_criteria(self, arguments: list[str]) -> None:
        self._require_count(arguments, 0)
        criteria = self._application.list_criteria()
        for criterion in criteria:
            self._write(
                f"{criterion.identifier}: {criterion.name}; "
                f"максимум {criterion.maximum_score.value}; вес {criterion.weight.value}"
            )
        if not criteria:
            self._write("Рубрикатор пуст.")

    def _assign_evaluation(self, arguments: list[str]) -> None:
        self._require_count(arguments, 3, 4)
        self._application.assign_evaluation(
            arguments[0],
            arguments[1],
            self._number(arguments[2]),
            arguments[3] if len(arguments) == 4 else "",
        )
        self._write("Оценка выставлена.")

    def _correct_evaluation(self, arguments: list[str]) -> None:
        self._require_count(arguments, 3, 4)
        self._application.correct_evaluation(
            arguments[0],
            arguments[1],
            self._number(arguments[2]),
            arguments[3] if len(arguments) == 4 else "",
        )
        self._write("Оценка исправлена.")

    def _cancel_evaluation(self, arguments: list[str]) -> None:
        self._require_count(arguments, 2)
        self._application.cancel_evaluation(arguments[0], arguments[1])
        self._write("Оценка отменена.")

    def _list_evaluations(self, arguments: list[str]) -> None:
        self._require_count(arguments, 1)
        evaluations = self._application.list_evaluations(arguments[0])
        for evaluation in evaluations:
            self._write(
                f"{evaluation.criterion_identifier}: {evaluation.score.value}"
                + (f" — {evaluation.comment}" if evaluation.comment else "")
            )
        if not evaluations:
            self._write("Оценок пока нет.")

    def _total(self, arguments: list[str]) -> None:
        self._require_count(arguments, 1, 2)
        mode = self._mode(arguments[1:])
        result = self._application.calculate_score(arguments[0], mode)
        self._write(
            f"{format_mode(mode)}: {format_score(result.value)} / 10; "
            f"оценено {result.evaluated_criteria}/{result.total_criteria}."
        )

    def _report(self, arguments: list[str]) -> None:
        self._require_count(arguments, 0, 1)
        report = self._application.build_report(self._mode(arguments))
        self._write(format_mode(report.mode))
        for row in report.rows:
            self._write(
                f"{row.student_identifier}: {row.student_name} — {format_score(row.score)}; "
                f"оценено {row.evaluated_criteria}/{row.total_criteria}"
            )
        if not report.rows:
            self._write("Студентов пока нет.")

    def _export(self, arguments: list[str]) -> None:
        self._require_count(arguments, 1, 2)
        destination = Path(arguments[0])
        count = self._application.export_report(destination, self._mode(arguments[1:]))
        self._write(f"Экспортировано студентов: {count}. Файл: {destination}")

    def _help(self, arguments: list[str]) -> None:
        self._require_count(arguments, 0)
        self._write(HELP)
