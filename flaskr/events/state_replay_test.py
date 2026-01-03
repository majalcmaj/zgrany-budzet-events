import pytest

from flaskr.events.event_store import DefaultEventStore
from flaskr.events.replay_wrapper import NoopEventRepository, ReplayWrapper
from flaskr.planning.planning_aggregate import PlanningAggregate, PlanningStatus


@pytest.mark.skip("This makes no sense with kurrentdb around. Rethink this")
def test_state_replay() -> None:
    event_store = ReplayWrapper(DefaultEventStore(NoopEventRepository()))
    planning_aggregate = PlanningAggregate("1234")

    event_store.replay_events("test_data/test_events.jsonl")

    assert planning_aggregate.status == PlanningStatus.FINISHED
