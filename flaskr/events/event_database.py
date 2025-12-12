import json


class EventDatabase:
    def __init__(self, file_path: str):
        self._events_file = open(file_path, "a")

    def store(self, event):
        event_type = type(event)
        # Serialize event to JSON
        event_json = json.dumps(
            {
                "module": event_type.__module__,
                "type": event_type.__name__,
                "payload": event.__dict__,
            }
        )
        self._events_file.write(event_json + "\n")
        self._events_file.flush()

    def destroy(self):
        self._events_file.flush()
        self._events_file.close()
