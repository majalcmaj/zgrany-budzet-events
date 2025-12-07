
from enum import Enum
class PlanningStatus(Enum):
    NOT_STARTED = "planning_not_started"
    IN_PROGRESS = "planning_in_progress"
    IN_REVIEW = "in_review_by_minister"
    NEEDS_CORRECTION = "needs_correction"
    FINISHED = "finished"

class PlanningState:
    def __init__(self):
        self.deadline = None
        self.status = PlanningStatus.NOT_STARTED
        self.correction_comment = None

    def set_deadline(self, date_str):
        self.deadline = date_str

    def start_planning(self):
        self.status = PlanningStatus.IN_PROGRESS
        self.correction_comment = None
        # Side effect: Reset office approvals
        from src.expenses import EXPENSES_CLOSED
        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = False

    def submit_to_minister(self):
        self.status = PlanningStatus.IN_REVIEW
        # Side effect: Reset office approvals
        from src.expenses import EXPENSES_CLOSED
        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = True

    def request_correction(self, comment=None):
        self.status = PlanningStatus.NEEDS_CORRECTION
        self.correction_comment = comment
        # Side effect: Reset office approvals
        from src.expenses import EXPENSES_CLOSED
        for office in EXPENSES_CLOSED:
            EXPENSES_CLOSED[office] = False

    def approve(self):
        self.status = PlanningStatus.FINISHED

    def reopen(self):
        self.status = PlanningStatus.NOT_STARTED
