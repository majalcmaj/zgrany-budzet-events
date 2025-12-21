from logging import getLogger
from uuid import uuid4

from flaskr.constants import OFFICES
from flaskr.planning.expenses.aggregate import (
    ExpenseListCreated,
    expense_list_stream_id,
)
from flaskr.planning.planning_aggregate import (
    PlanningScheduled,
    planning_aggregate_stream_id,
)

from ..events import events
from ..events.types import Command, Event

logger = getLogger(__name__)

__all__ = ["PlanningService"]


class PlanningService:
    def execute(self, command: Command) -> None:
        from .planning_aggregate import get_planning_aggregate

        event_list = get_planning_aggregate().process(command)
        events().emit(event_list)

    def schedule_planning(self):
        logger.warning("Scheduling planning")

        planning_id = str(uuid4())

        events().emit(
            [
                PlanningScheduled(
                    stream_id=planning_aggregate_stream_id(planning_id),
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
