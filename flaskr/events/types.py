from dataclasses import dataclass
from typing import ClassVar


@dataclass
class Event:
    type: ClassVar[str] = "EVENT"
    stream_id: str


@dataclass
class Command:
    aggregate_id: str
