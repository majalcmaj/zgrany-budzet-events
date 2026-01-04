from typing import Optional

from kurrentdbclient import NewEvent, StreamState

from flaskr.events import get_kurrent_client
from flaskr.events.serialisation import deserialise_event, serialise_event
from flaskr.events.types import Event
from flaskr.planning.planning_aggregate import (
    PlanningAggregate,
    PlanningScheduled,
    planning_id_to_stream,
    stream_to_planning_id,
)


class PlanningRepository:
    def get_planning(self, planning_id: str) -> PlanningAggregate:
        stream = get_kurrent_client().read_stream(planning_id_to_stream(planning_id))
        aggregate = PlanningAggregate(planning_id)
        for event in stream:
            domain_event = deserialise_event(event.type, event.data.decode())
            aggregate.apply(domain_event)
        print("Agg dict:", aggregate.__dict__, "Planning id: ", planning_id)
        return aggregate

    def get_current_planning(self) -> Optional[PlanningAggregate]:
        try:
            started_event = next(
                get_kurrent_client().read_all(
                    filter_include=PlanningScheduled.type, backwards=True
                )
            )
            return self.get_planning(stream_to_planning_id(started_event.stream_name))
        except StopIteration:
            return None

    def store(self, events: list[Event]) -> None:
        kurrent = get_kurrent_client()
        for event in events:
            k_event = NewEvent(event.type, data=serialise_event(event).encode())
            kurrent.append_event(
                stream_name=event.stream_id,
                event=k_event,
                current_version=StreamState.ANY,
            )
