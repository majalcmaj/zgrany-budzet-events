from .event_store import EventStore


class TestEvent:
    def __init__(self, id: int):
        self.id = id


class TestEvent2:
    def __init__(self, id: int):
        self.id = id


class TestEvent3:
    def __init__(self, id: int):
        self.id = id


class Subscriber:
    def __init__(self):
        self.handled_events = []

    def handle_test_event(self, event: TestEvent):
        self.handled_events.append(event)

    def handle_test_event2(self, event: TestEvent2):
        self.handled_events.append(event)

    def handle_test_event3(self, event: TestEvent3):
        self.handled_events.append(event)


def test_single_event_multiple_subscribers():
    event_store = EventStore()
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.handle_test_event)
    event_store.add_subscriber(subscriber2.handle_test_event)

    event_store.emit(TestEvent(1))

    assert subscriber1.handled_events == [TestEvent(1)]
    assert subscriber2.handled_events == [TestEvent(1)]


def test_many_events():
    event_store = EventStore()
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.handle_test_event)
    event_store.add_subscriber(subscriber1.handle_test_event2)
    event_store.add_subscriber(subscriber2.handle_test_event)
    event_store.add_subscriber(subscriber2.handle_test_event2)

    event_store.emit(TestEvent(1))
    event_store.emit(TestEvent2(1))
    event_store.emit(TestEvent(2))

    assert subscriber1.handled_events == [TestEvent(1), TestEvent2(1), TestEvent(2)]
    assert subscriber2.handled_events == [TestEvent(1), TestEvent2(1), TestEvent(2)]


def test_different_events():
    event_store = EventStore()
    subscriber1 = Subscriber()
    subscriber2 = Subscriber()
    event_store.add_subscriber(subscriber1.handle_test_event)
    event_store.add_subscriber(subscriber1.handle_test_event2)
    event_store.add_subscriber(subscriber2.handle_test_event2)
    event_store.add_subscriber(subscriber2.handle_test_event3)

    event_store.emit(TestEvent(1))
    event_store.emit(TestEvent2(2))
    event_store.emit(TestEvent3(3))

    assert subscriber1.handled_events == [TestEvent(1), TestEvent2(2)]
    assert subscriber2.handled_events == [TestEvent2(2), TestEvent3(3)]
