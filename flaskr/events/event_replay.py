import json
import importlib
from .event_store import EventStore


def replay_events(event_store: EventStore, file_path: str):
    with open(file_path, "r") as file:
        for line in file:
            event_data = json.loads(line)
            event_type = event_data["type"]
            event_module = event_data["module"]
            event_class = getattr(importlib.import_module(event_module), event_type)
            event = event_class(**event_data["payload"])
            event_store.emit(event)
