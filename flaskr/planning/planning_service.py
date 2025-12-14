from flaskr.events import events

from .planning_aggregate import Command, planning_aggregate

__all__ = ["PlanningService", "planning_service"]


class PlanningService:
    def __init__(self):
        self._event_store = events()
        self._planning_aggregate = planning_aggregate

    def execute(self, command: Command) -> None:
        events = self._planning_aggregate.process(command)
        self._event_store.emit(events)


planning_service = PlanningService()
