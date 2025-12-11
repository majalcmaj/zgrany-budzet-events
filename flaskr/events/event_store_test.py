from dataclasses import dataclass
from .event_store import EventStore


@dataclass
class TestEvent:
    def __init__(self, id: int):
        self.id = id


def test_single_event_multiple_observers():
    event_store = EventStore()

    class TestObserver:
        def __init__(self):
            self.handled_events = []

        @event_store.subscribe(TestEvent)
        def handle_test_event(self, event: TestEvent):
            self.handled_events.append(event)

    observer1 = TestObserver()
    observer2 = TestObserver()
    event_store.emit(TestEvent(1))

    assert observer1.handled_events == [TestEvent(1)]
    assert observer2.handled_events == [TestEvent(1)]


def test_many_events():
    event_store = EventStore()

    class TestObserver:
        def __init__(self):
            self.handled_events = []

        @event_store.subscribe(TestEvent)
        def handle_test_event(self, event: TestEvent):
            self.handled_events.append(event)

    observer1 = TestObserver()
    observer2 = TestObserver()
    event_store.emit(TestEvent(1))
    event_store.emit(TestEvent(2))
    event_store.emit(TestEvent(3))

    assert observer1.handled_events == [TestEvent(1), TestEvent(2), TestEvent(3)]
    assert observer2.handled_events == [TestEvent(1), TestEvent(2), TestEvent(3)]


def test_different_events():
    event_store = EventStore()

    @dataclass
    class TestEvent2:
        def __init__(self, id: int):
            self.id = id

    @dataclass
    class TestEvent3:
        def __init__(self, id: int):
            self.id = id

    class TestObserver:
        def __init__(self):
            self.handled_events = []

        @event_store.subscribe(TestEvent)
        def handle_test_event(self, event: TestEvent):
            self.handled_events.append(event)

        @event_store.subscribe(TestEvent2)
        def handle_test_event2(self, event: TestEvent2):
            self.handled_events.append(event)

    class TestObserver2:
        def __init__(self):
            self.handled_events = []

        @event_store.subscribe(TestEvent2)
        def handle_test_event2(self, event: TestEvent2):
            self.handled_events.append(event)

        @event_store.subscribe(TestEvent3)
        def handle_test_event3(self, event: TestEvent3):
            self.handled_events.append(event)

    observer1 = TestObserver()
    observer2 = TestObserver2()
    event_store.emit(TestEvent(1))
    event_store.emit(TestEvent2(2))
    event_store.emit(TestEvent3(3))

    assert observer1.handled_events == [TestEvent(1), TestEvent2(2)]
    assert observer2.handled_events == [TestEvent2(2), TestEvent3(3)]
