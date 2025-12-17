from ..events import events
from ..events.types import Command

__all__ = ["PlanningService"]


class PlanningService:
    def execute(self, command: Command) -> None:
        from .planning_aggregate import get_planning_aggregate

        event_list = get_planning_aggregate().process(command)
        events().emit(event_list)
