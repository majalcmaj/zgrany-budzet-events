import importlib
import json
from typing import Any, Callable, List

from .event_repository import EventRepository
from .event_store import EventStore


class ReplayWrapper(EventStore):
    def __init__(self, event_store: EventStore):
        self._event_store = event_store

    def add_subscriber(self, stream_id: str, handler: Callable[[Any], None]) -> None:
        self._event_store.add_subscriber(stream_id, handler)

    def remove_subscriber(self, stream_id: str, handler: Callable[[Any], None]) -> bool:
        return self._event_store.remove_subscriber(stream_id, handler)

    def emit(self, events: List[Any]) -> None:
        pass

    def destroy(self) -> None:
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
                print(f"Replaying event: {event_type} from data {event_data}")
                event = event_class(
                    **{"stream_id": event_data["stream_id"], **event_data["payload"]}
                )
                self._event_store.emit([event])


class NoopEventRepository(EventRepository):
    def store(self, event: Any) -> None:
        pass

    def destroy(self) -> None:
        pass
