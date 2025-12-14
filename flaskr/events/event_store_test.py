from typing import Generator

import pytest

from .event_store import DefaultEventStore
from .replay_wrapper import NoopEventRepository


class MockEvent:
    def __init__(self, id: int):
        self.id = id

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MockEvent) and self.id == other.id


class MockEvent2(MockEvent):
    def __init__(self, id: int):
        super().__init__(id)


class MockEvent3(MockEvent):
    def __init__(self, id: int):
        super().__init__(id)


class Subscriber:
    def __init__(self) -> None:
        self.handled_events: list[MockEvent] = []

    def handle_test_event(self, event: MockEvent) -> None:
        self.handled_events.append(event)

    def handle_test_event2(self, event: MockEvent2) -> None:
        self.handled_events.append(event)

    def handle_test_event3(self, event: MockEvent3) -> None:
        self.handled_events.append(event)


@pytest.fixture
def event_store() -> Generator[DefaultEventStore, None, None]:
    store = DefaultEventStore(NoopEventRepository())
    yield store
    store.destroy()


def test_single_event_multiple_subscribers(event_store: DefaultEventStore) -> None:
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.handle_test_event)
    event_store.add_subscriber(subscriber2.handle_test_event)

    event_store.emit([MockEvent(1)])

    assert subscriber1.handled_events == [MockEvent(1)]
    assert subscriber2.handled_events == [MockEvent(1)]


def test_many_events(event_store: DefaultEventStore) -> None:
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.handle_test_event)
    event_store.add_subscriber(subscriber1.handle_test_event2)
    event_store.add_subscriber(subscriber2.handle_test_event)
    event_store.add_subscriber(subscriber2.handle_test_event2)

    event_store.emit([MockEvent(1), MockEvent2(1), MockEvent(2)])

    assert subscriber1.handled_events == [MockEvent(1), MockEvent2(1), MockEvent(2)]
    assert subscriber2.handled_events == [MockEvent(1), MockEvent2(1), MockEvent(2)]


def test_different_events(event_store: DefaultEventStore) -> None:
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.handle_test_event)
    event_store.add_subscriber(subscriber1.handle_test_event2)
    event_store.add_subscriber(subscriber2.handle_test_event2)
    event_store.add_subscriber(subscriber2.handle_test_event3)

    event_store.emit([MockEvent(1), MockEvent2(2), MockEvent3(3)])

    assert subscriber1.handled_events == [MockEvent(1), MockEvent2(2)]
    assert subscriber2.handled_events == [MockEvent2(2), MockEvent3(3)]


def test_subscibing_function(event_store: DefaultEventStore) -> None:
    events_handled: list[MockEvent] = []

    def handle_test_event(event: MockEvent) -> None:
        events_handled.append(event)

    event_store.add_subscriber(handle_test_event)

    event_store.emit([MockEvent(1)])

    assert events_handled == [MockEvent(1)]


def test_remove_subscriber(event_store: DefaultEventStore) -> None:
    """Test that remove_subscriber correctly removes handlers."""
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()

    event_store.add_subscriber(subscriber1.handle_test_event)
    event_store.add_subscriber(subscriber2.handle_test_event)

    # Emit an event - both should receive it
    event_store.emit([MockEvent(1)])
    assert subscriber1.handled_events == [MockEvent(1)]
    assert subscriber2.handled_events == [MockEvent(1)]

    # Remove subscriber1
    result = event_store.remove_subscriber(subscriber1.handle_test_event)
    assert result is True

    # Emit another event - only subscriber2 should receive it
    event_store.emit([MockEvent(2)])
    assert subscriber1.handled_events == [MockEvent(1)]  # No change
    assert subscriber2.handled_events == [MockEvent(1), MockEvent(2)]

    # Try to remove subscriber1 again - should return False
    result = event_store.remove_subscriber(subscriber1.handle_test_event)
    assert result is False
