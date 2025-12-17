from dataclasses import dataclass, field
from logging import getLogger

from flask import Flask, current_app

from flaskr.planning.planning_service import PlanningService
from flaskr.planning.types import Expense

from .planning.planning_aggregate import PlanningAggregate

logger = getLogger(__name__)


@dataclass
class Context:
    planning_service = PlanningService()
    planning_aggregate: PlanningAggregate | None = None
    expense_lists: list[Expense] = field(default_factory=list)  # type: ignore


def init_context_extension(app: Flask) -> None:
    assert app is not None, "Flask app is required"
    if "context-extension" in app.extensions:
        raise ValueError("context-extension is already registered")

    app.extensions["context-extension"] = Context()
    logger.info("context-extension is registered")


def ctx() -> Context:
    context = current_app.extensions["context-extension"]
    assert context is not None, "Context needs to be initialised before use!"
    return context
