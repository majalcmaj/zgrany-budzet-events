from .types import Expense, PlanningStatus
from ..constants import OFFICES
from ..events import events
from dataclasses import dataclass

EXPENSES: dict[str, list[Expense]] = {office: [] for office in OFFICES}
EXPENSES_CLOSED = {office: False for office in OFFICES}


@dataclass
class _PlanningStartedEvent:
    deadline: str


class PlanningState:
    def __init__(self):
        # TODO: Move to main.py after cleanup
        self.event_store = events()
        self.deadline = None
        self.status = PlanningStatus.NOT_STARTED
        self.correction_comment = None
        self.planning_year = 2025
        self.event_store.add_subscriber(self.handle_planning_started)

    def start_planning(self, deadline: str):
        if self.status not in (
            PlanningStatus.NOT_STARTED,
            PlanningStatus.NEEDS_CORRECTION,
        ):
            raise ValueError(
                f"Planning is in state {self.status}, cannot start unless it is in state NOT_STARTED or NEEDS_CORRECTION"
            )
        self.event_store.emit(_PlanningStartedEvent(deadline))
        self.status = PlanningStatus.IN_PROGRESS

    def handle_planning_started(self, event: _PlanningStartedEvent):
        self.deadline = event.deadline
        self.status = PlanningStatus.IN_PROGRESS

        # Side effect: Reset office approvals - shouls be refactored?
        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = False

    def submit_to_minister(self):
        self.status = PlanningStatus.IN_REVIEW
        # Side effect: Reset office approvals

        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = True

    def request_correction(self, comment=None):
        self.correction_comment = comment
        if self.status != PlanningStatus.IN_REVIEW:
            return
        self.status = PlanningStatus.NEEDS_CORRECTION
        # Side effect: Reset office approvals
        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = False

    def approve(self):
        self.status = PlanningStatus.FINISHED
        self.correction_comment = None
        self.planning_year += 1

    def reopen(self):
        self.status = PlanningStatus.NOT_STARTED


planning_state = PlanningState()
