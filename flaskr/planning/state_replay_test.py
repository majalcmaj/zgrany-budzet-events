from ..events.event_store import DefaultEventStore
from ..planning.state import PlanningState, PlanningStatus
from ..events.event_replay import replay_events


def test_replay():
    event_store = DefaultEventStore()
    planning_state = PlanningState(event_store)

    replay_events(event_store, "test_data/test_events.jsonl")

    assert planning_state.status == PlanningStatus.FINISHED
