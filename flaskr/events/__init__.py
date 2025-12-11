from flask import current_app
from .event_store import EventStore
from logging import getLogger

logger = getLogger(__name__)


def init_event_extension(app):
    assert app is not None, "Flask app is required"
    if "event-extension" in app.extensions:
        raise ValueError("EventExtension is already registered")
    logger.info("EventExtension is registered")
    app.extensions["event-extension"] = EventStore()


def events() -> EventStore:
    if "event-extension" not in current_app.extensions:
        raise ValueError("EventExtension is not registered")
    return current_app.extensions["event-extension"]
