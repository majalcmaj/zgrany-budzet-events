from typing import Protocol, runtime_checkable
from typing import Callable, Any
import inspect
from .event_repository import EventRepository
from logging import getLogger
import threading

logger = getLogger(__name__)

__all__ = ["EventStore", "DefaultEventStore"]


@runtime_checkable
class EventStore(Protocol):
    def add_subscriber(self, handler: Callable[[Any], None]) -> None: ...
    def remove_subscriber(self, handler: Callable[[Any], None]) -> bool: ...
    def emit(self, event: Any) -> None: ...
    def destroy(self) -> None: ...


class DefaultEventStore(EventStore):
    def __init__(self, event_repository: EventRepository) -> None:
        # Dictionary mapping event types to lists of handler functions
        self._subscribers: dict[type, list[Callable[[Any], None]]] = {}
        self._event_repository = event_repository
        self._lock = threading.Lock()

    def add_subscriber(self, handler: Callable[[Any], None]) -> None:
        """
        Add a subscriber handler function.
        The handler's first parameter type annotation determines which event type it handles.
        """
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())

        if not params:
            raise ValueError("Handler must accept at least one parameter (the event)")

        # Get the type annotation of the first parameter
        event_type = params[0].annotation

        if event_type == inspect.Parameter.empty:
            raise ValueError("Handler's first parameter must have a type annotation")

        with self._lock:
            # Add the handler to the list of subscribers for this event type
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            self._subscribers[event_type].append(handler)

    def remove_subscriber(self, handler: Callable[[Any], None]) -> bool:
        """
        Remove a subscriber handler function.
        Returns True if the handler was found and removed, False otherwise.
        """
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())

        if not params:
            return False

        event_type = params[0].annotation

        if event_type == inspect.Parameter.empty:
            return False

        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                    return True
                except ValueError:
                    return False
            return False

    def emit(self, event: Any) -> None:
        """
        Emit an event: persist it to the database and notify all registered handlers.
        """
        with self._lock:
            self._event_repository.store(event)
        self._notify_subscribers(event)

    def _notify_subscribers(self, event: Any) -> None:
        """
        Notify all registered handlers for the event type without persisting.
        Used internally and by replay functionality.
        """
        event_type = type(event)

        with self._lock:
            handlers = self._subscribers.get(event_type, []).copy()

        logger.debug(f"Notifying {len(handlers)} handlers for {event_type.__name__}")

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Handler {handler.__name__ if hasattr(handler, '__name__') else handler} "
                    f"failed for {event_type.__name__}: {e}",
                    exc_info=True,
                )

    def destroy(self) -> None:
        self._event_repository.destroy()
