import pytest
import threading
import time

from werkzeug.serving import make_server
from main import app, db
from planning.planning_workflow import PlanningState, PlanningStatus
from expenses import EXPENSES, EXPENSES_CLOSED
from constants import OFFICES


class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = make_server("127.0.0.1", 5001, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()


@pytest.fixture(scope="session")
def base_url():
    return "http://127.0.0.1:5001"


@pytest.fixture(scope="session", autouse=True)
def server():
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

    # Give it a moment to start
    time.sleep(1)

    yield st

    st.shutdown()


@pytest.fixture(autouse=True)
def reset_state():
    # Reset application state before each test
    from planning import planning_state

    # Reset planning state
    planning_state.status = PlanningStatus.NOT_STARTED
    planning_state.deadline = None
    planning_state.correction_comment = None
    planning_state.planning_year = 2025

    # Reset expenses
    for office in OFFICES:
        EXPENSES[office] = []
        EXPENSES_CLOSED[office] = False

    yield
