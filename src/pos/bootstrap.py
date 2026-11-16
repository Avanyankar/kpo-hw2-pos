import punq

from pos.adapters.csv_export import CsvReportExporter
from pos.adapters.memory import InMemoryRubricRepository, InMemoryStudentRepository
from pos.application.facade import GradingFacade
from pos.application.ports import ReportExporter, RubricRepository, StudentRepository
from pos.domain.scoring import FinalScoreCalculator, FinalScorePolicy, PreliminaryScorePolicy


def build_container() -> punq.Container:
    container = punq.Container()
    container.register(StudentRepository, instance=InMemoryStudentRepository())
    container.register(RubricRepository, instance=InMemoryRubricRepository())
    container.register(ReportExporter, CsvReportExporter)
    container.register(FinalScoreCalculator)
    container.register(FinalScorePolicy)
    container.register(PreliminaryScorePolicy)
    container.register(GradingFacade)
    return container


def build_application() -> GradingFacade:
    return build_container().resolve(GradingFacade)
