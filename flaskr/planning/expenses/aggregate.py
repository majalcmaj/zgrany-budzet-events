import logging
from dataclasses import dataclass

from ...events import events
from ...events.types import Event
from ..planning_aggregate import Command, PlanningScheduled
from ..types import Expense, ExpensesStatus

logger = logging.getLogger(__name__)

__all__ = [
    "ExpensesAggregate",
    "AddExpenseCommand",
]


@dataclass
class ExpenseAdded(Event):
    expense: Expense


@dataclass
class AddExpenseCommand(Command):
    expense: Expense


def expense_stream_id(expense_id: str | None) -> str:
    assert expense_id is not None
    return f"expenses-{expense_id}"


class ExpensesAggregate:
    def __init__(self):
        self.id: str | None = None
        self.expenses: list[Expense] = []
        self.status: ExpensesStatus = ExpensesStatus.NOT_STARTED

    def process(self, command: Command) -> list[Event]:

        match command:
            case AddExpenseCommand(expense=expense):
                if self.status == ExpensesStatus.IN_PROGRESS:
                    return [ExpenseAdded(expense_stream_id(self.id), expense)]
                raise ValueError(
                    f"Cannot add expense when not in progress; status: {self.status}"
                )
            case _:
                return []


expenses_aggregetes: dict[str, ExpensesAggregate] = {}


def planning_scheduled_listener(event: PlanningScheduled) -> None:
    logger.warning(
        f"Creating expenses aggregates for planning id {event.planning_year}"
    )
    for office in event.offices:
        expense_agg = ExpensesAggregate()
        expense_agg.id = f"{event.planning_year}-{office}"
        expenses_aggregetes[expense_agg.id] = expense_agg
        logger.warning(
            f"Created expenses aggregate with id {expense_agg.id} for office {office}"
        )


events().add_subscriber("planning_scheduled", planning_scheduled_listener)
