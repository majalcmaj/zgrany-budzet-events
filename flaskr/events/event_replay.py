import json
import importlib
from .event_store import EventStore
from typing import Callable, Any


class ReplayEventStore(EventStore):

    def __init__(self, event_store: EventStore):
        self._event_store = event_store

    def add_subscriber(self, handler: Callable[[Any], None]) -> None:
        self._event_store.add_subscriber(handler)

    def emit(self, event: Any) -> None:
        pass

    def destroy(self):
        self._event_store.destroy()

    def emit_with_no_new_events(self, event: Any) -> None:
        self._event_store.emit(event)


def replay_events(event_store: EventStore, file_path: str):
    replay_event_store = ReplayEventStore(event_store)
    with open(file_path, "r") as file:
        for line in file:
            event_data = json.loads(line)
            event_type = event_data["type"]
            event_module = event_data["module"]
            event_class = getattr(importlib.import_module(event_module), event_type)
            event = event_class(**event_data["payload"])
            replay_event_store.emit_with_no_new_events(event)
