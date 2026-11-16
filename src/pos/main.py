import argparse
import sys
from pathlib import Path

from pos.adapters.console import CommandProcessor
from pos.bootstrap import build_application


def main() -> int:
    parser = argparse.ArgumentParser(description="ПОС — преподавательская оценка студентов")
    parser.add_argument("scenario", nargs="?", type=Path, help="файл команд в UTF-8")
    arguments = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    processor = CommandProcessor(build_application(), sys.stdout)
    if arguments.scenario is not None:
        try:
            with arguments.scenario.open(encoding="utf-8-sig") as stream:
                for line in stream:
                    if line.strip() and not line.lstrip().startswith("#"):
                        print(f"> {line.rstrip()}")
                    if not processor.execute(line):
                        break
        except (OSError, UnicodeError) as error:
            print(f"Не удалось прочитать сценарий: {error}", file=sys.stderr)
            return 1
        return int(processor.had_errors)
    print("ПОС. Справка: help. Данные хранятся в памяти до выхода.")
    try:
        while True:
            if not processor.execute(input("> ")):
                break
    except (EOFError, KeyboardInterrupt):
        print("\nРабота завершена.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
