from dataclasses import dataclass
from typing import Generator

import pytest

from .event_store import DefaultEventStore, EventStore
from .replay_wrapper import NoopEventRepository
from .types import Event


@dataclass
class MockEvent(Event):
    id: int

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MockEvent) and self.id == other.id


@dataclass
class OtherEvent(Event):
    id: int

    def __eq__(self, other: object) -> bool:
        return isinstance(other, OtherEvent) and self.id == other.id


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


def test_streams_do_not_leak_events(event_store: DefaultEventStore) -> None:
    subscriber = Subscriber()
    event_store.add_subscriber(subscriber.apply, "other_stream")
    events = [MockEvent("s", 1)]

    event_store.emit(events)

    assert subscriber.handled_events == []


def test_subscriber_receives_all_events_when_no_filtering_specified(
    event_store: EventStore,
):
    subscriber = Subscriber()
    event_store.add_subscriber(subscriber.apply)

    events = [
        MockEvent("some_stream", 1),
        MockEvent("other_stream", 2),
        OtherEvent("whatever_stream", 3),
    ]

    event_store.emit(events)

    assert subscriber.handled_events == events


def test_single_stream_many_subscribers(event_store: DefaultEventStore) -> None:
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.apply, "s")
    event_store.add_subscriber(subscriber2.apply, "s")
    events = [MockEvent("s", 1)]

    event_store.emit(events)

    assert subscriber1.handled_events == events
    assert subscriber2.handled_events == events


def test_many_events_in_stream(event_store: DefaultEventStore) -> None:
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.apply, "s")
    event_store.add_subscriber(subscriber2.apply, "s")
    events = [
        MockEvent("s", 1),
        MockEvent("s", 2),
        MockEvent("s", 3),
        OtherEvent("s", 4),
    ]

    event_store.emit(events)

    assert subscriber1.handled_events == events
    assert subscriber2.handled_events == events


def test_different_streams(event_store: DefaultEventStore) -> None:
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.apply, "stream1")
    event_store.add_subscriber(subscriber2.apply, "stream2")
    event_store.add_subscriber(subscriber1.apply, "common_stream")
    event_store.add_subscriber(subscriber2.apply, "common_stream")

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


def test_subscribing_by_type(event_store: EventStore) -> None:
    subscriber = Subscriber()
    event_store.add_subscriber(subscriber.apply, event_type=MockEvent)

    event_store.emit(
        [
            MockEvent("any_stream", 1),
            OtherEvent("other_stream", 2),
            MockEvent("yet_another", 3),
        ]
    )

    assert subscriber.handled_events == [
        MockEvent("any_stream", 1),
        MockEvent("yet_another", 3),
    ]


def test_remove_subscriber(event_store: DefaultEventStore) -> None:
    """Test that remove_subscriber correctly removes handlers."""
    # TODO: Add test for removing subscribers for all events and for types
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()

    event_store.add_subscriber(subscriber1.apply, "s")
    event_store.add_subscriber(subscriber2.apply, "s")

    # Emit an event - both should receive it
    event_store.emit([MockEvent("s", 1)])
    assert subscriber1.handled_events == [MockEvent("s", 1)]
    assert subscriber2.handled_events == [MockEvent("s", 1)]

    # Remove subscriber1
    result = event_store.remove_subscriber(subscriber1.apply, "s")
    assert result is True

    # Emit another event - only subscriber2 should receive it
    event_store.emit([MockEvent("s", 2)])
    assert subscriber1.handled_events == [MockEvent("s", 1)]  # No change
    assert subscriber2.handled_events == [MockEvent("s", 1), MockEvent("s", 2)]

    # Try to remove subscriber1 again - should return False
    result = event_store.remove_subscriber(subscriber1.apply, "s")
    assert result is False
