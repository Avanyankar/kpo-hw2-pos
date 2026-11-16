from decimal import ROUND_HALF_UP, Decimal

from pos.application.reports import ScoreMode


def format_score(value: Decimal | None) -> str:
    if value is None:
        return "не рассчитан"
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def format_mode(mode: ScoreMode) -> str:
    return "Окончательный итог" if mode == ScoreMode.FINAL else "Предварительный результат"
