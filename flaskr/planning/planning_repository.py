from flaskr.events import get_kurrent_client
from flaskr.events.serialisation import deserialise_event
from flaskr.planning.planning_aggregate import (
    PlanningAggregate,
    planning_id_to_stream,
)


class PlanningRepository:
    def get_planning(self, planning_id: str) -> PlanningAggregate:
        stream = get_kurrent_client().read_stream(planning_id_to_stream(planning_id))
        aggregate = PlanningAggregate(planning_id)
        for event in stream:
            domain_event = deserialise_event(event.type, event.data.decode())
            aggregate.apply(domain_event)
        return aggregate
