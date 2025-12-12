from ..events.event_store import DefaultEventStore
from ..planning.state import PlanningState, PlanningStatus
from ..events.replay_wrapper import ReplayWrapper


def test_replay():
    event_store = ReplayWrapper(DefaultEventStore())
    planning_state = PlanningState(event_store)

    event_store.replay_events("test_data/test_events.jsonl")

    assert planning_state.status == PlanningStatus.FINISHED
