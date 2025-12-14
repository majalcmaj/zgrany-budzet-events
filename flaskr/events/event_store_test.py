from dataclasses import dataclass
from typing import Generator

import pytest

from .event_store import DefaultEventStore
from .replay_wrapper import NoopEventRepository
from .types import Event


@dataclass
class MockEvent(Event):
    id: int

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MockEvent) and self.id == other.id


class Subscriber:
    def __init__(self) -> None:
        self.handled_events: list[MockEvent] = []

    def apply(self, event: MockEvent) -> None:
        self.handled_events.append(event)


@pytest.fixture
def event_store() -> Generator[DefaultEventStore, None, None]:
    store = DefaultEventStore(NoopEventRepository())
    yield store
    store.destroy()


def test_stream_without_subscribers(event_store: DefaultEventStore) -> None:
    subscriber = Subscriber()
    event_store.add_subscriber("other_stream", subscriber.apply)
    events = [MockEvent("s", 1)]

    event_store.emit(events)

    assert subscriber.handled_events == []


def test_single_stream_many_subscribers(event_store: DefaultEventStore) -> None:
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber("s", subscriber1.apply)
    event_store.add_subscriber("s", subscriber2.apply)
    events = [MockEvent("s", 1)]

    event_store.emit(events)

    assert subscriber1.handled_events == events
    assert subscriber2.handled_events == events


def test_many_events(event_store: DefaultEventStore) -> None:
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber("s", subscriber1.apply)
    event_store.add_subscriber("s", subscriber2.apply)
    events = [MockEvent("s", 1), MockEvent("s", 2), MockEvent("s", 3)]

    event_store.emit(events)

    assert subscriber1.handled_events == events
    assert subscriber2.handled_events == events


def test_different_streams(event_store: DefaultEventStore) -> None:
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber("stream1", subscriber1.apply)
    event_store.add_subscriber("stream2", subscriber2.apply)
    event_store.add_subscriber("common_stream", subscriber1.apply)
    event_store.add_subscriber("common_stream", subscriber2.apply)

    event_store.emit(
        [
            MockEvent("stream1", 1),
            MockEvent("stream2", 2),
            MockEvent("common_stream", 3),
        ]
    )

    assert subscriber1.handled_events == [
        MockEvent("stream1", 1),
        MockEvent("common_stream", 3),
    ]
    assert subscriber2.handled_events == [
        MockEvent("stream2", 2),
        MockEvent("common_stream", 3),
    ]


def test_remove_subscriber(event_store: DefaultEventStore) -> None:
    """Test that remove_subscriber correctly removes handlers."""
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()

    event_store.add_subscriber("s", subscriber1.apply)
    event_store.add_subscriber("s", subscriber2.apply)

    # Emit an event - both should receive it
    event_store.emit([MockEvent("s", 1)])
    assert subscriber1.handled_events == [MockEvent("s", 1)]
    assert subscriber2.handled_events == [MockEvent("s", 1)]

    # Remove subscriber1
    result = event_store.remove_subscriber("s", subscriber1.apply)
    assert result is True

    # Emit another event - only subscriber2 should receive it
    event_store.emit([MockEvent("s", 2)])
    assert subscriber1.handled_events == [MockEvent("s", 1)]  # No change
    assert subscriber2.handled_events == [MockEvent("s", 1), MockEvent("s", 2)]

    # Try to remove subscriber1 again - should return False
    result = event_store.remove_subscriber("s", subscriber1.apply)
    assert result is False
