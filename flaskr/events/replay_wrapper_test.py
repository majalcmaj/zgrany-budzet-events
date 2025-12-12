from .replay_wrapper import ReplayWrapper
from .event_store import DefaultEventStore, EventStore
from .replay_wrapper import NoopEventRepository


class MockEvent:
    def __init__(self, id: int):
        self.id = id

    def __eq__(self, other):
        return isinstance(other, MockEvent) and self.id == other.id


class MockSubscriber:
    def __init__(self, event_store: EventStore):
        self.handled_events: list[MockEvent] = []
        event_store.add_subscriber(self.handle_test_event)
        self.event_store = event_store

    def handle_test_event(self, event: MockEvent):
        self.handled_events.append(event)
        self.event_store.emit(MockEvent(21))


def test_replay():
    event_store = ReplayWrapper(DefaultEventStore(NoopEventRepository()))
    subscriber = MockSubscriber(event_store)

    event_store.replay_events("test_data/test_replay.jsonl")

    assert subscriber.handled_events == [MockEvent(1), MockEvent(2)]
