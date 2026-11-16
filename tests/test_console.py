import os
import subprocess
from io import StringIO
from pathlib import Path

import pytest

from pos.adapters.console import CommandProcessor
from pos.bootstrap import build_application


@pytest.mark.parametrize(
    "command",
    [
        "unknown",
        "student add",
        'student add s1 "',
        "total s1 other",
        "evaluation set s1 exam not-a-number",
        "evaluation set s1 exam NaN",
        "evaluation set s1 exam 11",
        "evaluation set s1 unknown 1",
        "evaluation change s1 exam 1",
        "evaluation remove s1 exam",
        "exit unexpected",
    ],
)
def test_bad_command_does_not_stop_session_or_change_grades(command: str) -> None:
    output = StringIO()
    application = build_application()
    processor = CommandProcessor(application, output)
    processor.execute('student add s1 "Анна Иванова"')
    processor.execute('criterion add exam "Экзамен" 10 1')
    assert processor.execute(command)
    assert processor.had_errors
    assert "Ошибка:" in output.getvalue()
    assert application.list_evaluations("s1") == ()
    processor.execute("evaluation set s1 exam 8")
    processor.execute("total s1")
    assert "8.00 / 10" in output.getvalue()


def test_comments_quoted_names_and_exit() -> None:
    output = StringIO()
    application = build_application()
    processor = CommandProcessor(application, output)
    assert processor.execute("# Пример")
    assert processor.execute('student add s1 "Анна #1" # комментарий')
    assert application.list_students()[0].name == "Анна #1"
    assert not processor.execute("exit")


def run_program(
    arguments: list[str], directory: Path, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    import sys

    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "pos.main", *arguments],
        cwd=directory,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
        timeout=15,
    )


def test_demo_runs_and_exports_results(tmp_path: Path) -> None:
    scenario = Path(__file__).resolve().parents[1] / "scenarios" / "demo.txt"
    result = run_program([str(scenario)], tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "7.70 / 10" in result.stdout
    assert "8.60 / 10" in result.stdout
    assert "3.20 / 10" in result.stdout
    assert (tmp_path / "results.csv").is_file()


def test_scenario_errors_return_nonzero_but_continue(tmp_path: Path) -> None:
    scenario = tmp_path / "invalid.txt"
    scenario.write_text('unknown\nstudent add s1 "Анна"\nstudent list\n', encoding="utf-8")
    result = run_program([str(scenario)], tmp_path)
    assert result.returncode == 1
    assert "s1: Анна" in result.stdout
    missing = run_program([str(tmp_path / "missing.txt")], tmp_path)
    assert missing.returncode == 1
    assert "Traceback" not in missing.stderr


def test_interactive_input_and_end_of_input(tmp_path: Path) -> None:
    result = run_program([], tmp_path, 'student add s1 "Анна"\nstudent list\n')
    assert result.returncode == 0
    assert "s1: Анна" in result.stdout
