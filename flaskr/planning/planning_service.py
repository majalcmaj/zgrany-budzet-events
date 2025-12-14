from flaskr.events import events

from .planning_aggregate import StartPlanningCommand, planning_aggregate

__all__ = ["PlanningService", "planning_service"]


class PlanningService:
    def __init__(self):
        self._event_store = events()
        self._planning_aggregate = planning_aggregate

    def start_planning(self, deadline: str) -> None:
        if not deadline:
            raise ValueError("Deadline must be provided to start planning.")

        command = StartPlanningCommand(
            aggregate_id="planning_aggregate", deadline=deadline
        )
        events = self._planning_aggregate.process(command)
        self._event_store.emit(events)


planning_service = PlanningService()
