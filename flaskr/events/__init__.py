from flask import current_app, Flask
from .event_store import EventStore, DefaultEventStore
from .event_repository import FileEventRepository
from logging import getLogger
import atexit
from typing import cast

logger = getLogger(__name__)

__all__ = ["init_event_extension", "events", "EventStore"]


def init_event_extension(app: Flask) -> None:
    assert app is not None, "Flask app is required"
    if "event-extension" in app.extensions:
        raise ValueError("EventExtension is already registered")
    logger.info("EventExtension is registered")
    # Allow configuration of events file path, default to events.jsonl
    events_file = app.config.get("EVENTS_FILE", "events.jsonl")
    event_store = DefaultEventStore(FileEventRepository(events_file))
    app.extensions["event-extension"] = event_store
    atexit.register(event_store.destroy)


def events() -> EventStore:
    if "event-extension" not in current_app.extensions:
        raise ValueError("EventExtension is not registered")
    assert isinstance(current_app.extensions["event-extension"], EventStore)
    return current_app.extensions["event-extension"]
