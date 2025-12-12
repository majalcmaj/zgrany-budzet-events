from typing import Protocol
from typing import Callable, Any
import inspect
from .event_database import EventDatabase
from logging import getLogger

logger = getLogger(__name__)


class EventStore(Protocol):
    def add_subscriber(self, handler: Callable[[Any], None]) -> None: ...
    def emit(self, event: Any) -> None: ...
    def destroy(self) -> None: ...


class DefaultEventStore(EventStore):
    def __init__(self) -> None:
        # Dictionary mapping event types to lists of handler functions
        self._subscribers: dict[type, list[Callable[[Any], None]]] = {}
        self._event_database = EventDatabase("events.jsonl")

    def add_subscriber(self, handler: Callable[[Any], None]) -> None:
        """
        Add a subscriber handler function.
        The handler's first parameter type annotation determines which event type it handles.
        """
        # Get the handler's signature
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())

        if not params:
            raise ValueError("Handler must accept at least one parameter (the event)")

        # Get the type annotation of the first parameter
        event_type = params[0].annotation

        if event_type == inspect.Parameter.empty:
            raise ValueError("Handler's first parameter must have a type annotation")

        # Add the handler to the list of subscribers for this event type
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(handler)

    def emit(self, event: Any) -> None:
        """
        Emit an event to all registered handlers for that event type.
        """
        event_type = type(event)

        # Get all handlers for this event type
        handlers = self._subscribers.get(event_type, [])

        self._event_database.store(event)

        # Call each handler with the event
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler {handler} failed with exception: {e}")

    def destroy(self):
        self._event_database.destroy()
