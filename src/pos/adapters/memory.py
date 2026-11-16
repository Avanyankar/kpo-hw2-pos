from pos.application.errors import ApplicationError
from pos.domain.rubric import Rubric
from pos.domain.students import Student


class InMemoryStudentRepository:
    def __init__(self) -> None:
        self._students: dict[str, Student] = {}

    def add(self, student: Student) -> None:
        if student.identifier in self._students:
            raise ApplicationError(f"Студент «{student.identifier}» уже существует.")
        self._students[student.identifier] = student

    def get(self, identifier: str) -> Student:
        try:
            return self._students[identifier]
        except KeyError as error:
            raise ApplicationError(f"Студент «{identifier}» не найден.") from error

    def list_students(self) -> tuple[Student, ...]:
        return tuple(self._students.values())

    def save(self, student: Student) -> None:
        self.get(student.identifier)
        self._students[student.identifier] = student


class InMemoryRubricRepository:
    def __init__(self) -> None:
        self._rubric = Rubric()

    def get(self) -> Rubric:
        return self._rubric

    def save(self, rubric: Rubric) -> None:
        self._rubric = rubric
