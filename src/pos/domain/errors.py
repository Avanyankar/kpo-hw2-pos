class DomainError(Exception):
    pass


class IncompleteAssessmentError(DomainError):
    def __init__(self, missing_criteria: tuple[str, ...]) -> None:
        self.missing_criteria = missing_criteria
        super().__init__("Не выставлены оценки по критериям: " + ", ".join(missing_criteria))
