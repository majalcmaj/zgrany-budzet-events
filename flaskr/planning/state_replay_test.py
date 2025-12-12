from ..events.event_store import EventStore
from ..planning.state import PlanningState, PlanningStatus


def test_replay():
    event_store = EventStore()
    planning_state = PlanningState(event_store)

    event_store.replay_events("test_data/events.jsonl")

    assert planning_state.status == PlanningStatus.FINISHED
