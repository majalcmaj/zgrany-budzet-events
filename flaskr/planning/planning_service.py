from logging import getLogger
from typing import Optional
from uuid import uuid4

from flaskr.constants import OFFICES
from flaskr.planning.expenses.aggregate import (
    ExpenseListCreated,
    expense_list_stream_id,
)
from flaskr.planning.planning_aggregate import (
    PlanningAggregate,
    PlanningScheduled,
    planning_id_to_stream,
)
from flaskr.planning.planning_repository import PlanningRepository

from ..events.types import Command, Event

logger = getLogger(__name__)

__all__ = ["PlanningService"]


class PlanningService:

    def __init__(self) -> None:
        self._planning_repository = PlanningRepository()

    def get_current_planning(self) -> Optional[PlanningAggregate]:
        return self._planning_repository.get_current_planning()

    def execute(self, command: Command) -> None:
        planning = self._planning_repository.get_current_planning()
        if planning is None:
            raise ValueError("No planning found")

        event_list = planning.process(command)
        self._planning_repository.store(event_list)

    def schedule_planning(self):
        logger.warning("Scheduling planning")

        planning_id = str(uuid4())

        self._planning_repository.store(
            [
                PlanningScheduled(
                    stream_id=planning_id_to_stream(planning_id),
                    id=planning_id,
                    planning_year=2025,
                    offices=OFFICES,
                ),
                *self._create_expenses(planning_id),
            ],
        )

    def _create_expenses(self, planning_aggregate_id: str) -> list[Event]:
        return [
            ExpenseListCreated(
                stream_id=expense_list_stream_id(id),
                expense_list_id=id,
                office=office,
                parent_planning_id=planning_aggregate_id,
            )
            for id, office in map(lambda o: (o, str(uuid4)), OFFICES)
        ]
