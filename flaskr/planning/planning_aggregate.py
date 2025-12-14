from dataclasses import dataclass

from ..constants import OFFICES
from ..events import EventStore, events
from .types import Expense, PlanningStatus

__all__ = [
    "PlanningStatus",
    "EXPENSES",
    "EXPENSES_CLOSED",
    "planning_aggregate",
    "PlanningAggregate",
]

EXPENSES: dict[str, list[Expense]] = {office: [] for office in OFFICES}
EXPENSES_CLOSED = {office: False for office in OFFICES}


class ExpenseAggregate:
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.expenses: list[Expense] = []

    def add_expense(self, expense: Expense) -> None:
        self.expenses.append(expense)


@dataclass
class _PlanningStartedEvent:
    deadline: str


class _PlanningSubmittedEvent:
    pass


class _PlanningApprovedEvent:
    pass


@dataclass
class _InitialMinisterGuidanceEvent:
    comment: str


@dataclass
class _MinisterCorrectionRequestedEvent:
    comment: str


class _PlanningReopenedEvent:
    pass


@dataclass
class _ExpenseAggregatesAssignedEvent:
    office_ids: list[str]


class PlanningAggregate:
    def __init__(self, event_store: EventStore | None = None):
        # TODO: Move to main.py after cleanup
        self.event_store = event_store or events()
        self.deadline: str | None = None
        self.status = PlanningStatus.NOT_STARTED
        self.correction_comment: str | None = None
        self.planning_year = 2025
        self.office_expense_ids: dict[str, str] = {}
        self.event_store.add_subscriber(self._handle_planning_started)
        self.event_store.add_subscriber(self._handle_submitted_to_minister)
        self.event_store.add_subscriber(self._handle_approved)
        self.event_store.add_subscriber(self._handle_initial_minister_guidance)
        self.event_store.add_subscriber(self._handle_minister_correction_requested)
        self.event_store.add_subscriber(self._handle_planning_reopened)

    def start_planning(self, deadline: str) -> None:
        if self.status not in (
            PlanningStatus.NOT_STARTED,
            PlanningStatus.NEEDS_CORRECTION,
        ):
            raise ValueError(
                f"Planning is in state {self.status}, cannot start unless it is in state NOT_STARTED or NEEDS_CORRECTION"
            )
        if not deadline:
            raise ValueError("Deadline is required")

        self.event_store.emit(_PlanningStartedEvent(deadline))

    def _handle_planning_started(self, event: _PlanningStartedEvent) -> None:
        self.deadline = event.deadline
        self.status = PlanningStatus.IN_PROGRESS

        # Side effect: Reset office approvals - shouls be refactored?
        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = False

    def submit_to_minister(self) -> None:
        if self.status != PlanningStatus.IN_PROGRESS:
            raise ValueError(
                f"Planning is in state {self.status}, cannot submit unless it is in state IN_PROGRESS"
            )
        self.event_store.emit(_PlanningSubmittedEvent())

    def _handle_submitted_to_minister(self, _: _PlanningSubmittedEvent) -> None:
        self.status = PlanningStatus.IN_REVIEW
        # Side effect: Reset office approvals

        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = True

    def request_correction(self, comment: str) -> None:
        if self.status == PlanningStatus.NOT_STARTED:
            self.event_store.emit(_InitialMinisterGuidanceEvent(comment))
        elif self.status == PlanningStatus.IN_REVIEW:
            self.event_store.emit(_MinisterCorrectionRequestedEvent(comment))

    def _handle_initial_minister_guidance(
        self, event: _InitialMinisterGuidanceEvent
    ) -> None:
        self.correction_comment = event.comment

    def _handle_minister_correction_requested(
        self, event: _MinisterCorrectionRequestedEvent
    ) -> None:
        self.correction_comment = event.comment
        self.status = PlanningStatus.NEEDS_CORRECTION
        # Side effect: Reset office approvals
        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = False

    def approve(self) -> None:
        if self.status != PlanningStatus.IN_REVIEW:
            raise ValueError(
                f"Planning is in state {self.status}, cannot approve unless it is in state IN_REVIEW"
            )
        self.event_store.emit(_PlanningApprovedEvent())

    def _handle_approved(self, _: _PlanningApprovedEvent) -> None:
        self.status = PlanningStatus.FINISHED
        self.correction_comment = None
        self.planning_year += 1

    def reopen(self) -> None:
        if self.status != PlanningStatus.FINISHED:
            raise ValueError(
                f"Planning is in state {self.status}, cannot reopen unless it is in state FINISHED"
            )
        self.event_store.emit(_PlanningReopenedEvent())

    def _handle_planning_reopened(self, _: _PlanningReopenedEvent) -> None:
        self.status = PlanningStatus.NOT_STARTED

    def assign_expense_aggregates(self, office_ids: list[str]) -> None:
        if self.status != PlanningStatus.NOT_STARTED:
            raise ValueError(
                f"Planning is in state {self.status}, cannot assign expense aggregates unless it is in state NOT_STARTED"
            )
        self.event_store.emit(_ExpenseAggregatesAssignedEvent(office_ids))

    def _handle_expense_aggregates_assigned(
        self, event: _ExpenseAggregatesAssignedEvent
    ) -> None:
        self.office_expense_ids = {
            office_id: office_id for office_id in event.office_ids
        }


planning_aggregate = PlanningAggregate()
expense_aggregates: dict[str, ExpenseAggregate] = {
    office: ExpenseAggregate(aggregate_id=office) for office in OFFICES
}
planning_aggregate.assign_expense_aggregates(OFFICES)
