import json
import importlib
from .event_store import EventStore
from typing import Callable, Any


class ReplayWrapper(EventStore):
    def __init__(self, event_store: EventStore):
        self._event_store = event_store

    def add_subscriber(self, handler: Callable[[Any], None]) -> None:
        self._event_store.add_subscriber(handler)

    def emit(self, event: Any) -> None:
        pass

    def destroy(self):
        self._event_store.destroy()

    def replay_events(self, file_path: str):
        with open(file_path, "r") as file:
            for line in file:
                event_data = json.loads(line)
                event_type = event_data["type"]
                event_module = event_data["module"]
                event_class = getattr(importlib.import_module(event_module), event_type)
                event = event_class(**event_data["payload"])
                self._event_store.emit(event)
