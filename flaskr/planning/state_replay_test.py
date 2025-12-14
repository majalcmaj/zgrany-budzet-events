from ..events.event_store import DefaultEventStore
from ..events.replay_wrapper import NoopEventRepository, ReplayWrapper
from ..planning.planning_aggregate import PlanningState, PlanningStatus


def test_state_replay() -> None:
    event_store = ReplayWrapper(DefaultEventStore(NoopEventRepository()))
    planning_state = PlanningState(event_store)

    event_store.replay_events("test_data/test_events.jsonl")

    assert planning_state.status == PlanningStatus.FINISHED
