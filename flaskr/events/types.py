from dataclasses import dataclass


@dataclass
class Event:
    stream_id: str


@dataclass
class Command:
    aggregate_id: str
