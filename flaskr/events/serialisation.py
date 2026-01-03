import json
from typing import Dict, Type

from flaskr.events.types import Event

event_types: Dict[str, Type[Event]] = {}


def event(cls: Type[Event], type: str) -> Type[Event]:
    if type in event_types:
        raise ValueError(
            f"Cannot register {cls} as event type {type} - type already taken by {event_types[type]} "
        )
    event_types[type] = cls
    cls.type = type
    return cls


def serialise_event(event: Event) -> str:
    cls = type(event)
    if cls.type not in event_types:
        raise ValueError(
            f"Event of type {cls.type} and class {cls} must be annotated with @event"
        )

    try:
        payload = event.__dict__
    except AttributeError:
        # Handle objects with __slots__ or other special cases
        if hasattr(event, "to_dict"):
            payload = event.to_dict()  # type:ignore[misc]
        else:
            raise ValueError(
                f"Event of type {cls} must have __dict__ or to_dict() method"
            )

    return json.dumps(payload)


def deserialise_event(type: str, payload: str) -> Event:
    cls = event_types[type]
    kws = json.loads(payload)
    return cls(**kws)
