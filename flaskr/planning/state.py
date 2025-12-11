from .types import Expense, PlanningStatus
from ..constants import OFFICES

EXPENSES: dict[str, list[Expense]] = {office: [] for office in OFFICES}
EXPENSES_CLOSED = {office: False for office in OFFICES}


class PlanningState:
    def __init__(self):
        self.deadline = None
        self.status = PlanningStatus.NOT_STARTED
        self.correction_comment = None
        self.planning_year = 2025

    def set_deadline(self, date_str):
        self.deadline = date_str

    def start_planning(self):
        self.status = PlanningStatus.IN_PROGRESS
        # Side effect: Reset office approvals

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
