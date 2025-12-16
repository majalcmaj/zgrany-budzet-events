import threading
import time
from typing import Generator

import pytest
from flask import Flask
from werkzeug.serving import make_server

from flaskr.constants import OFFICES
from flaskr.main import app, db
from flaskr.planning.planning_aggregate import (
    EXPENSES,
    EXPENSES_CLOSED,
    PlanningStatus,
    planning_aggregate,
)


class ServerThread(threading.Thread):
    def __init__(self, app: Flask) -> None:
        threading.Thread.__init__(self)
        self.server = make_server("127.0.0.1", 5001, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self) -> None:
        self.server.serve_forever()

    def shutdown(self) -> None:
        self.server.shutdown()


@pytest.fixture(scope="session")
def base_url() -> str:
    return "http://127.0.0.1:5001"


@pytest.fixture(scope="session", autouse=True)
def server() -> Generator[ServerThread, None, None]:
    # Configure app for testing
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for easier testing if needed

    # Initialize DB
    with app.app_context():
        db.create_all()

    # Start server
    st = ServerThread(app)
    st.start()

    # Give it a moment to start #TODO: remove the sleep!!!
    time.sleep(1)

    yield st

    st.shutdown()


@pytest.fixture(autouse=True)
def reset_state() -> Generator[None, None, None]:
    assert planning_aggregate is not None
    planning_aggregate.status = PlanningStatus.NOT_STARTED
    planning_aggregate.deadline = None
    planning_aggregate.correction_comment = None
    planning_aggregate.planning_year = 2025

    # Reset expenses
    for office in OFFICES:
        EXPENSES[office] = []
        EXPENSES_CLOSED[office] = False

    yield
