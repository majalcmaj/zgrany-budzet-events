import json
import importlib
from .event_store import EventStore
from .event_repository import EventRepository
from typing import Callable, Any


class ReplayWrapper(EventStore):
    def __init__(self, event_store: EventStore):
        self._event_store = event_store

    def add_subscriber(self, handler: Callable[[Any], None]) -> None:
        self._event_store.add_subscriber(handler)

    def remove_subscriber(self, handler: Callable[[Any], None]) -> bool:
        return self._event_store.remove_subscriber(handler)

    def emit(self, event: Any) -> None:
        pass

    def destroy(self):
        self._event_store.destroy()

    def replay_events(self, file_path: str) -> None:
        """
        Replay events from a file by notifying subscribers without re-persisting.
        This prevents duplicate events in the database and duplicate side effects.
        """
        with open(file_path, "r") as file:
            for line in file:
                event_data = json.loads(line)
                event_type = event_data["type"]
                event_module = event_data["module"]
                event_class = getattr(importlib.import_module(event_module), event_type)
                event = event_class(**event_data["payload"])
                self._event_store.emit(event)


class NoopEventRepository(EventRepository):
    def store(self, event: Any) -> None:
        pass

    def destroy(self) -> None:
        pass
