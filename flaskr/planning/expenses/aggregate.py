import logging
from dataclasses import dataclass

from ...events import events
from ...events.types import Event
from ..planning_aggregate import Command, PlanningScheduled
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


def expense_list_stream_id(expense_id: str | None) -> str:
    assert expense_id is not None
    return f"expenses-{expense_id}"


class ExpenseListAggregate:
    def __init__(self):
        self.id: str | None = None
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
            case _:
                return []


expenses_aggregates: dict[str, ExpenseListAggregate] = {}


def expense_list_created_listener(event: ExpenseListCreated) -> None:
    logger.warning(f"Creating expense list aggregate for id {event.expense_list_id}")
    aggregate = ExpenseListAggregate()
    aggregate.id = event.expense_list_id
    expenses_aggregates[event.expense_list_id] = aggregate


events().add_subscriber("expense_list_created", expense_list_created_listener)


def office_year_to_expense_list_id(office_id: str, year: int) -> str:
    return f"expenses-{office_id}-{year}"


def planning_scheduled_listener(event: PlanningScheduled) -> None:
    logger.warning(
        f"Creating expenses aggregates for planning id {event.planning_year}"
    )
    events().emit(
        [
            ExpenseListCreated(
                stream_id="expense_list_created",
                expense_list_id=expense_list_stream_id(id),
                parent_planning_id=str(event.planning_year),
            )
            for id in map(
                lambda office: office_year_to_expense_list_id(
                    office, event.planning_year
                ),
                event.offices,
            )
        ]
    )


events().add_subscriber("planning_scheduled", planning_scheduled_listener)
