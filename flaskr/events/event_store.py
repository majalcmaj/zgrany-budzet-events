import threading
from logging import getLogger
from typing import Any, Callable, List, Protocol, TypeVar, runtime_checkable

from .event_repository import EventRepository
from .types import Event

logger = getLogger(__name__)

__all__ = ["EventStore", "DefaultEventStore", "TEvent"]

TEvent = TypeVar("TEvent", bound=Event, covariant=True)

_ALL_STREAMS = "__all_streams__"


@runtime_checkable
class EventStore(Protocol):
    def add_subscriber(
        self, handler: Callable[[TEvent], None], stream_id: str = _ALL_STREAMS
    ) -> None: ...
    def remove_subscriber(
        self, stream_id: str, handler: Callable[[TEvent], None]
    ) -> bool: ...
    def emit(self, events: List[TEvent]) -> None: ...
    def destroy(self) -> None: ...


class DefaultEventStore(EventStore):
    def __init__(self, event_repository: EventRepository) -> None:
        # Dictionary mapping event types to lists of handler functions
        self._subscribers: dict[str, list[Callable[[Any], None]]] = {}
        self._event_repository = event_repository
        self._lock = threading.Lock()

    def add_subscriber(
        self, handler: Callable[[TEvent], None], stream_id: str = _ALL_STREAMS
    ) -> None:
        """
        Add a subscriber handler function.
        """

        with self._lock:
            # Add the handler to the list of subscribers for this event type
            self._subscribers.setdefault(stream_id, []).append(handler)

    def remove_subscriber(
        self, stream_id: str, handler: Callable[[TEvent], None]
    ) -> bool:
        """
        Remove a subscriber handler function.
        Returns True if the handler was found and removed, False otherwise.
        """
        with self._lock:
            if stream_id in self._subscribers:
                try:
                    self._subscribers[stream_id].remove(handler)
                    return True
                except ValueError:
                    return False
            return False

    def emit(self, events: List[TEvent]) -> None:
        """
        Emit an event: persist it to the database and notify all registered handlers.
        """

        for event in events:
            with self._lock:
                self._event_repository.store(event)
            self._notify_subscribers(event)

    def _notify_subscribers(self, event: Event) -> None:
        """
        Notify all registered handlers for the event type without persisting.
        Used internally and by replay functionality.
        """
        with self._lock:
            handlers = [  # type: ignore[misc]
                *self._subscribers.get(event.stream_id, []),
                *self._subscribers.get(_ALL_STREAMS, []),
            ]
        # type: ignore[misc],
        logger.debug(
            f"Notifying {len(handlers)} handlers for stream_id {event.stream_id}"
        )

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Handler {handler.__name__ if hasattr(handler, '__name__') else handler} "
                    f"failed for {event.stream_id}: {e}",
                    exc_info=True,
                )

    def destroy(self) -> None:
        self._event_repository.destroy()
