from .event_store import EventStore


class MockEvent:
    def __init__(self, id: int):
        self.id = id

    def __eq__(self, other):
        return isinstance(other, MockEvent) and self.id == other.id


class MockEvent2(MockEvent):
    def __init__(self, id: int):
        super().__init__(id)


class MockEvent3(MockEvent):
    def __init__(self, id: int):
        super().__init__(id)


class Subscriber:
    def __init__(self):
        self.handled_events = []

    def handle_test_event(self, event: MockEvent):
        self.handled_events.append(event)

    def handle_test_event2(self, event: MockEvent2):
        self.handled_events.append(event)

    def handle_test_event3(self, event: MockEvent3):
        self.handled_events.append(event)


def test_single_event_multiple_subscribers():
    event_store = EventStore()
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.handle_test_event)
    event_store.add_subscriber(subscriber2.handle_test_event)

    event_store.emit(MockEvent(1))

    assert subscriber1.handled_events == [MockEvent(1)]
    assert subscriber2.handled_events == [MockEvent(1)]


def test_many_events():
    event_store = EventStore()
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.handle_test_event)
    event_store.add_subscriber(subscriber1.handle_test_event2)
    event_store.add_subscriber(subscriber2.handle_test_event)
    event_store.add_subscriber(subscriber2.handle_test_event2)

    event_store.emit(MockEvent(1))
    event_store.emit(MockEvent2(1))
    event_store.emit(MockEvent(2))

    assert subscriber1.handled_events == [MockEvent(1), MockEvent2(1), MockEvent(2)]
    assert subscriber2.handled_events == [MockEvent(1), MockEvent2(1), MockEvent(2)]


def test_different_events():
    event_store = EventStore()
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.handle_test_event)
    event_store.add_subscriber(subscriber1.handle_test_event2)
    event_store.add_subscriber(subscriber2.handle_test_event2)
    event_store.add_subscriber(subscriber2.handle_test_event3)

    event_store.emit(MockEvent(1))
    event_store.emit(MockEvent2(2))
    event_store.emit(MockEvent3(3))

    assert subscriber1.handled_events == [MockEvent(1), MockEvent2(2)]
    assert subscriber2.handled_events == [MockEvent2(2), MockEvent3(3)]


def test_non_class_method():
    event_store = EventStore()
    events_handled = []

    def handle_test_event(event: MockEvent):
        events_handled.append(event)

    event_store.add_subscriber(handle_test_event)

    event_store.emit(MockEvent(1))

    assert events_handled == [MockEvent(1)]
