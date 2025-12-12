import json
from typing import Any
from typing import Protocol


class EventRepository(Protocol):
    def store(self, event: Any) -> None: ...
    def destroy(self) -> None: ...


class FileEventRepository(EventRepository):
    def __init__(self, file_path: str = "events.jsonl"):
        self._file_path = file_path
        self._events_file = open(file_path, "a")

    def store(self, event: Any) -> None:
        event_type = type(event)
        # Serialize event to JSON
        # Try to use __dict__, but allow for custom serialization
        try:
            payload = event.__dict__
        except AttributeError:
            # Handle objects with __slots__ or other special cases
            if hasattr(event, "to_dict"):
                payload = event.to_dict()
            else:
                raise ValueError(
                    f"Event {event_type.__name__} must have __dict__ or to_dict() method"
                )

        event_json = json.dumps(
            {
                "module": event_type.__module__,
                "type": event_type.__name__,
                "payload": payload,
            }
        )
        self._events_file.write(event_json + "\n")
        self._events_file.flush()

    def destroy(self) -> None:
        self._events_file.flush()
        self._events_file.close()
