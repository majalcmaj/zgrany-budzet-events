import logging
from dataclasses import dataclass

from ..constants import OFFICES
from ..events import EventStore, events
from ..events.types import Command, Event
from .types import Expense, PlanningStatus

logger = logging.getLogger(__name__)

__all__ = [
    "PlanningStatus",
    "EXPENSES",
    "EXPENSES_CLOSED",
    "PlanningAggregate",
]

EXPENSES: dict[str, list[Expense]] = {office: [] for office in OFFICES}
EXPENSES_CLOSED = {office: False for office in OFFICES}


@dataclass
class PlanningScheduled(Event):
    planning_year: int
    offices: list[str]


@dataclass
class PlanningStartedEvent(Event):
    deadline: str


@dataclass
class PlanningSubmittedEvent(Event):
    pass


@dataclass
class PlanningApprovedEvent(Event):
    pass


@dataclass
class InitialMinisterGuidanceEvent(Event):
    comment: str


@dataclass
class MinisterCorrectionRequestedEvent(Event):
    comment: str


@dataclass
class PlanningReopenedEvent(Event):
    pass


@dataclass
class _ExpenseAggregatesAssignedEvent(Event):
    office_ids: list[str]


@dataclass
class StartPlanningCommand(Command):
    deadline: str


class SubmitToMinisterCommand(Command):
    pass


class ApprovePlanningCommand(Command):
    pass


class ReopenPlanningCommand(Command):
    pass


@dataclass
class AssignExpenseAggregatesCommand(Command):
    office_ids: list[str]


@dataclass
class RequestCorrectionCommand(Command):
    comment: str


def planning_aggregate_stream_id(agg_id: str) -> str:
    return "pl_agg_" + agg_id


class PlanningAggregate:
    def __init__(self, event_store: EventStore):
        # TODO: Move to main.py after cleanup
        self.id = "2025"
        self.stream_id = planning_aggregate_stream_id(self.id)
        self.deadline: str | None = None
        self.status = PlanningStatus.NOT_STARTED
        self.correction_comment: str | None = None
        self.planning_year = 2025
        self.office_expense_ids: dict[str, str] = {}
        event_store.add_subscriber(self.stream_id, self._apply)

    def process(self, command: Command) -> list[Event]:
        match command:
            case StartPlanningCommand() as cmd:
                return self.start_planning(cmd.deadline)
            case SubmitToMinisterCommand():
                return self.submit_to_minister()
            case ApprovePlanningCommand():
                return self.approve()
            case ReopenPlanningCommand():
                return self.reopen()
            case RequestCorrectionCommand() as cmd:
                return self.request_correction(cmd.comment)
            case _:
                return []

    def start_planning(self, deadline: str) -> list[Event]:
        if self.status not in (
            PlanningStatus.NOT_STARTED,
            PlanningStatus.NEEDS_CORRECTION,
        ):
            raise ValueError(
                f"Planning is in state {self.status}, cannot start unless it is in state NOT_STARTED or NEEDS_CORRECTION"
            )
        if not deadline:
            raise ValueError("Deadline is required")

        return [PlanningStartedEvent(stream_id=self.stream_id, deadline=deadline)]

    def submit_to_minister(self) -> list[Event]:
        if self.status != PlanningStatus.IN_PROGRESS:
            raise ValueError(
                f"Planning is in state {self.status}, cannot submit unless it is in state IN_PROGRESS"
            )
        return [PlanningSubmittedEvent(stream_id=self.stream_id)]

    def approve(self) -> list[Event]:
        if self.status != PlanningStatus.IN_REVIEW:
            raise ValueError(
                f"Planning is in state {self.status}, cannot approve unless it is in state IN_REVIEW"
            )
        return [PlanningApprovedEvent(self.stream_id)]

    def request_correction(self, comment: str) -> list[Event]:
        if self.status == PlanningStatus.NOT_STARTED:
            return [InitialMinisterGuidanceEvent(self.stream_id, comment)]
        elif self.status == PlanningStatus.IN_REVIEW:
            return [MinisterCorrectionRequestedEvent(self.stream_id, comment)]
        return []

    def reopen(self) -> list[Event]:
        if self.status != PlanningStatus.FINISHED:
            raise ValueError(
                f"Planning is in state {self.status}, cannot reopen unless it is in state FINISHED"
            )
        return [PlanningReopenedEvent(self.stream_id)]

    def _apply(self, event: Event) -> None:
        match event:
            case PlanningStartedEvent() as e:
                self._handle_planning_started(e)
            case PlanningSubmittedEvent() as e:
                self._handle_submitted_to_minister(e)
            case PlanningApprovedEvent() as e:
                self._handle_approved(e)
            case InitialMinisterGuidanceEvent() as e:
                self._handle_initial_minister_guidance(e)
            case MinisterCorrectionRequestedEvent() as e:
                self._handle_minister_correction_requested(e)
            case PlanningReopenedEvent() as e:
                self._handle_planning_reopened(e)
            case _ExpenseAggregatesAssignedEvent() as e:
                self._handle_expense_aggregates_assigned(e)
            case _:
                logger.error(
                    f"Got unhandled event type: {type(event)} in stream {event.stream_id}"
                )

    def _handle_planning_started(self, event: PlanningStartedEvent) -> None:
        self.deadline = event.deadline
        self.status = PlanningStatus.IN_PROGRESS

        # Side effect: Reset office approvals - shouls be refactored?
        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = False

    def _handle_submitted_to_minister(self, _: PlanningSubmittedEvent) -> None:
        self.status = PlanningStatus.IN_REVIEW
        # Side effect: Reset office approvals

        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = True

    def _handle_initial_minister_guidance(
        self, event: InitialMinisterGuidanceEvent
    ) -> None:
        self.correction_comment = event.comment

    def _handle_minister_correction_requested(
        self, event: MinisterCorrectionRequestedEvent
    ) -> None:
        self.correction_comment = event.comment
        self.status = PlanningStatus.NEEDS_CORRECTION
        # Side effect: Reset office approvals
        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = False

    def _handle_approved(self, _: PlanningApprovedEvent) -> None:
        self.status = PlanningStatus.FINISHED
        self.correction_comment = None
        self.planning_year += 1

    def _handle_planning_reopened(self, _: PlanningReopenedEvent) -> None:
        self.status = PlanningStatus.NOT_STARTED

    def _handle_expense_aggregates_assigned(
        self, event: _ExpenseAggregatesAssignedEvent
    ) -> None:
        self.office_expense_ids = {
            office_id: office_id for office_id in event.office_ids
        }


def planning_scheduled_listener(event: PlanningScheduled) -> None:
    logger.warning(
        f"Planning scheduled for year {event.planning_year} for offices {event.offices}"
    )

    from flaskr.extensions import ctx

    ctx().planning_aggregate = PlanningAggregate(events())


def get_planning_aggregate() -> PlanningAggregate:
    from flaskr.extensions import ctx

    agg = ctx().planning_aggregate
    assert agg is not None
    return agg
