from .types import Expense, PlanningStatus
from ..constants import OFFICES
from ..events import events
from dataclasses import dataclass

EXPENSES: dict[str, list[Expense]] = {office: [] for office in OFFICES}
EXPENSES_CLOSED = {office: False for office in OFFICES}


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


class PlanningState:
    def __init__(self):
        # TODO: Move to main.py after cleanup
        self.event_store = events()
        self.deadline = None
        self.status = PlanningStatus.NOT_STARTED
        self.correction_comment = None
        self.planning_year = 2025
        self.event_store.add_subscriber(self._handle_planning_started)
        self.event_store.add_subscriber(self._handle_submitted_to_minister)
        self.event_store.add_subscriber(self._handle_approved)
        self.event_store.add_subscriber(self._handle_initial_minister_guidance)
        self.event_store.add_subscriber(self._handle_minister_correction_requested)
        self.event_store.add_subscriber(self._handle_planning_reopened)

    def start_planning(self, deadline: str):
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
        self.status = PlanningStatus.IN_PROGRESS

    def _handle_planning_started(self, event: _PlanningStartedEvent):
        self.deadline = event.deadline
        self.status = PlanningStatus.IN_PROGRESS

        # Side effect: Reset office approvals - shouls be refactored?
        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = False

    def submit_to_minister(self):
        if self.status != PlanningStatus.IN_PROGRESS:
            raise ValueError(
                f"Planning is in state {self.status}, cannot submit unless it is in state IN_PROGRESS"
            )
        self.event_store.emit(_PlanningSubmittedEvent())

    def _handle_submitted_to_minister(self, _event: _PlanningSubmittedEvent):
        self.status = PlanningStatus.IN_REVIEW
        # Side effect: Reset office approvals

        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = True

    def request_correction(self, comment):
        if self.status == PlanningStatus.NOT_STARTED:
            self.event_store.emit(_InitialMinisterGuidanceEvent(comment))
        elif self.status == PlanningStatus.IN_REVIEW:
            self.event_store.emit(_MinisterCorrectionRequestedEvent(comment))

    def _handle_initial_minister_guidance(self, event: _InitialMinisterGuidanceEvent):
        self.correction_comment = event.comment

    def _handle_minister_correction_requested(
        self, event: _MinisterCorrectionRequestedEvent
    ):
        self.correction_comment = event.comment
        self.status = PlanningStatus.NEEDS_CORRECTION
        # Side effect: Reset office approvals
        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = False

    def approve(self):
        if self.status != PlanningStatus.IN_REVIEW:
            raise ValueError(
                f"Planning is in state {self.status}, cannot approve unless it is in state IN_REVIEW"
            )
        self.event_store.emit(_PlanningApprovedEvent())

    def _handle_approved(self, _event: _PlanningApprovedEvent):
        self.status = PlanningStatus.FINISHED
        self.correction_comment = None
        self.planning_year += 1

    def reopen(self):
        if self.status != PlanningStatus.FINISHED:
            raise ValueError(
                f"Planning is in state {self.status}, cannot reopen unless it is in state FINISHED"
            )
        self.event_store.emit(_PlanningReopenedEvent())

    def _handle_planning_reopened(self, _event: _PlanningReopenedEvent):
        self.status = PlanningStatus.NOT_STARTED


planning_state = PlanningState()
