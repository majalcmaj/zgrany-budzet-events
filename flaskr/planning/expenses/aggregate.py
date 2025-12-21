import logging
from dataclasses import dataclass

from ...events import events
from ...events.types import Event
from ..planning_aggregate import (
    Command,
    PlanningStartedEvent,
    PlanningSubmittedEvent,
)
from ..types import Expense, ExpensesStatus

logger = logging.getLogger(__name__)

__all__ = [
    "ExpenseListAggregate",
    "AddExpenseCommand",
]


@dataclass
class ExpenseAdded(Event):
    expense: Expense


@dataclass
class ExpenseListCreated(Event):
    expense_list_id: str
    parent_planning_id: str


@dataclass
class AddExpenseCommand(Command):
    expense: Expense


@dataclass
class RemoveExpenseCommand(Command):
    expense_id: str


@dataclass
class ExpenseRemovedEvent(Event):
    expense_id: str


def expense_list_stream_id(expense_id: str | None) -> str:
    assert expense_id is not None
    return f"expenses-{expense_id}"


class ExpenseListAggregate:
    def __init__(self, id: str, parent_planning_id: str):
        self.id = id
        self.parent_planning_id = parent_planning_id
        self.expenses: list[Expense] = []
        self.status: ExpensesStatus = ExpensesStatus.NOT_STARTED

    def process(self, command: Command) -> list[Event]:
        match command:
            case AddExpenseCommand(expense=expense):
                if self.status == ExpensesStatus.IN_PROGRESS:
                    return [ExpenseAdded(expense_list_stream_id(self.id), expense)]
                raise ValueError(
                    f"Cannot add expense when not in progress; status: {self.status}"
                )
            case RemoveExpenseCommand(expense_id=expense_id):
                if self.status == ExpensesStatus.IN_PROGRESS:
                    for i in range(len(self.expenses)):
                        if self.expenses[i].id == expense_id:
                            return [
                                ExpenseRemovedEvent(
                                    expense_list_stream_id(expense_id), expense_id
                                )
                            ]
                raise ValueError(
                    f"Cannot remove expense when not in progress; status: {self.status}"
                )
            case _:
                return []

    def _apply(self, event: Event) -> None:
        match event:
            case PlanningStartedEvent(planning_id=self.parent_planning_id):
                self.status = ExpensesStatus.IN_PROGRESS
            case PlanningSubmittedEvent(planning_id=self.parent_planning_id):
                self.status = ExpensesStatus.CLOSED
            case ExpenseRemovedEvent(expense_id=expense_id):
                for i in range(len(self.expenses)):
                    if self.expenses[i].id == expense_id:
                        del self.expenses[i]
            case _:
                return


expenses_aggregates: dict[str, ExpenseListAggregate] = {}


def expense_list_created_listener(event: ExpenseListCreated) -> None:
    logger.warning(f"Creating expense list aggregate for id {event.expense_list_id}")
    aggregate = ExpenseListAggregate(event.parent_planning_id, event.expense_list_id)
    expenses_aggregates[event.expense_list_id] = aggregate


events().add_subscriber("expense_list_created", expense_list_created_listener)


def office_year_to_expense_list_id(office_id: str, year: int) -> str:
    return f"expenses-{office_id}-{year}"
