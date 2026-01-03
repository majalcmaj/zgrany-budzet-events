import atexit
from logging import getLogger

from flask import Flask, current_app
from kurrentdbclient import KurrentDBClient

from .event_repository import FileEventRepository
from .event_store import DefaultEventStore, EventStore

logger = getLogger(__name__)

__all__ = ["init_event_extension", "events", "EventStore"]


def init_kurrentdb(app: Flask) -> None:
    assert app is not None
    if "kurrent-db" in app.extensions:
        raise ValueError("Kurrent Db already initialised")
    logger.info("Registering kurrentdb")
    app.extensions["kurrent-db"] = KurrentDBClient(
        uri="kurrentdb://localhost:2113?Tls=false"
    )


def init_event_extension(app: Flask) -> None:
    assert app is not None, "Flask app is required"
    if "event-extension" in app.extensions:
        raise ValueError("EventExtension is already registered")
    logger.info("EventExtension is registered")
    # Allow configuration of events file path, default to events.jsonl
    events_file: str = str(app.config.get("EVENTS_FILE", "events.jsonl"))  # type: ignore[misc]
    event_store = DefaultEventStore(FileEventRepository(events_file))
    app.extensions["event-extension"] = event_store
    atexit.register(event_store.destroy)


def events() -> EventStore:
    if "event-extension" not in current_app.extensions:
        raise ValueError("EventExtension is not registered")
    assert isinstance(current_app.extensions["event-extension"], EventStore)
    return current_app.extensions["event-extension"]
