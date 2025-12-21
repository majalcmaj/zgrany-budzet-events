from dataclasses import dataclass

from .event_store import DefaultEventStore, EventStore
from .replay_wrapper import NoopEventRepository, ReplayWrapper
from .types import Event


@dataclass
class MockEvent(Event):
    id: int

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MockEvent) and self.id == other.id


class MockSubscriber:
    def __init__(self, event_store: EventStore):
        self.handled_events: list[MockEvent] = []
        event_store.add_subscriber(self.handle_test_event, "s")
        self.event_store = event_store

    def handle_test_event(self, event: MockEvent) -> None:
        self.handled_events.append(event)
        self.event_store.emit([MockEvent("s", 21)])


def test_replay() -> None:
    event_store = ReplayWrapper(DefaultEventStore(NoopEventRepository()))
    subscriber = MockSubscriber(event_store)

    event_store.replay_events("test_data/test_replay.jsonl")

    assert subscriber.handled_events == [MockEvent("s", 1), MockEvent("s", 2)]
