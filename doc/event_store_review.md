# Event Store Code Review

**Review Date:** 2025-12-12  
**Scope:** `flaskr/events/` directory

---

## 🔴 Critical (Fix Before Production)

### 1. File Handle Leak
**Location:** [event_store.py:11](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py#L11)

**Problem:** File opened in `__init__` but only closed via `atexit`. Process crashes/kills = data loss.

**Fix:**
```python
# Option A: Context manager per operation
def emit(self, event):
    with open(self._events_file_path, 'a') as f:
        f.write(event_json + '\n')

# Option B: Explicit cleanup in tests
def test_example():
    store = EventStore()
    try:
        # test code
    finally:
        store.destroy()
```

**Resources:**
- [Python File I/O Best Practices](https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files)
- [Context Managers](https://docs.python.org/3/reference/datamodel.html#context-managers)

---

### 2. Hardcoded File Path
**Location:** [event_store.py:11](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py#L11)

**Problem:** All instances write to same `events.jsonl`. Tests interfere with each other.

**Fix:**
```python
def __init__(self, events_file: str = "events.jsonl"):
    self._events_file_path = events_file
    self._events_file = open(events_file, "w")
```

**Resources:**
- [Dependency Injection](https://python-dependency-injector.ets-labs.org/)
- [12-Factor App: Config](https://12factor.net/config)

---

### 3. Replay Re-triggers Side Effects
**Location:** [event_store.py:68](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py#L68)

**Problem:** `replay_events()` calls `emit()` → handlers execute again → duplicate emails/DB writes.

**Fix:**
```python
def emit(self, event: Any, persist: bool = True) -> None:
    if persist:
        self._persist_event(event)
    self._notify_subscribers(event)

def replay_events(self, file_path: str):
    # ... load event ...
    self.emit(event, persist=False)  # Don't re-persist
```

**Resources:**
- [Event Sourcing Patterns](https://martinfowler.com/eaaDev/EventSourcing.html)
- [CQRS Journey](https://docs.microsoft.com/en-us/previous-versions/msp-n-p/jj554200(v=pandp.10))

---

### 4. No Error Handling in Handlers
**Location:** [event_store.py:57-58](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py#L57-L58)

**Problem:** One failing handler stops all subsequent handlers.

**Fix:**
```python
for handler in handlers:
    try:
        handler(event)
    except Exception as e:
        logger.error(f"Handler {handler.__name__} failed: {e}", exc_info=True)
        # Continue processing other handlers
```

**Resources:**
- [Python Logging](https://docs.python.org/3/howto/logging.html)
- [Error Handling Best Practices](https://realpython.com/python-exceptions/)

---

## ⚠️ High Priority (Fix Soon)

### 5. No Thread Safety
**Location:** [event_store.py:10-11, 32-35, 44, 54](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py)

**Problem:** Flask is multi-threaded. Race conditions in `_subscribers` dict and file writes.

**Fix:**
```python
import threading

class EventStore:
    def __init__(self):
        self._lock = threading.RLock()
        # ...
    
    def add_subscriber(self, handler):
        with self._lock:
            # ... existing code ...
    
    def emit(self, event):
        with self._lock:
            # ... existing code ...
```

**Resources:**
- [Threading in Python](https://docs.python.org/3/library/threading.html)
- [Thread Safety in Flask](https://flask.palletsprojects.com/en/stable/design/#thread-locals)

---

### 6. Missing Unsubscribe
**Location:** [event_store.py](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py)

**Problem:** No way to remove subscribers → memory leaks in long-running apps.

**Fix:**
```python
def remove_subscriber(self, handler: Callable[[Any], None]) -> bool:
    sig = inspect.signature(handler)
    event_type = list(sig.parameters.values())[0].annotation
    
    if event_type in self._subscribers:
        try:
            self._subscribers[event_type].remove(handler)
            return True
        except ValueError:
            return False
    return False
```

**Resources:**
- [Observer Pattern](https://refactoring.guru/design-patterns/observer)
- [Memory Management in Python](https://realpython.com/python-memory-management/)

---

### 7. Fragile Event Serialization
**Location:** [event_store.py:51](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py#L51)

**Problem:** `event.__dict__` fails for `__slots__`, properties, nested objects.

**Fix:**
```python
# Option A: Protocol
from typing import Protocol

class Serializable(Protocol):
    def to_dict(self) -> dict: ...

def emit(self, event: Serializable):
    event_json = json.dumps({
        "module": event_type.__module__,
        "type": event_type.__name__,
        "payload": event.to_dict(),  # Use protocol
    })

# Option B: Dataclasses
from dataclasses import dataclass, asdict

@dataclass
class MyEvent:
    id: int
    
# Then use asdict(event)
```

**Resources:**
- [Python Protocols](https://peps.python.org/pep-0544/)
- [Dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [attrs Library](https://www.attrs.org/)

---

### 8. Test Cleanup Missing
**Location:** [event_store_test.py](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store_test.py)

**Problem:** Tests create `events.jsonl` files but never clean up.

**Fix:**
```python
import pytest
import tempfile
import os

@pytest.fixture
def event_store():
    # Use temp file for each test
    fd, path = tempfile.mkstemp(suffix='.jsonl')
    os.close(fd)
    
    store = EventStore(events_file=path)
    yield store
    
    store.destroy()
    os.unlink(path)

def test_single_event_multiple_subscribers(event_store):
    # Use fixture instead of creating new instance
    subscriber1 = Subscriber()
    # ...
```

**Resources:**
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [tempfile Module](https://docs.python.org/3/library/tempfile.html)

---

## 📝 Medium Priority (Quality Improvements)

### 9. Add Logging
**Location:** [event_store.py:37, 57](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py)

**Problem:** No visibility into event flow in production.

**Fix:**
```python
import logging

logger = logging.getLogger(__name__)

def emit(self, event: Any) -> None:
    event_type = type(event)
    logger.debug(f"Emitting {event_type.__name__}: {event.__dict__}")
    
    handlers = self._subscribers.get(event_type, [])
    logger.info(f"Notifying {len(handlers)} handlers for {event_type.__name__}")
    # ...
```

**Resources:**
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [Structured Logging](https://www.structlog.org/)

---

### 10. Add Event Metadata
**Location:** [event_store.py:47-53](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py#L47-L53)

**Problem:** No timestamps, correlation IDs, or versioning for debugging/tracing.

**Fix:**
```python
import uuid
from datetime import datetime, timezone

def emit(self, event: Any) -> None:
    event_json = json.dumps({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "module": event_type.__module__,
        "type": event_type.__name__,
        "payload": event.__dict__,
    })
```

**Resources:**
- [Event Versioning](https://leanpub.com/esversioning/read)
- [Correlation IDs](https://hilton.org.uk/blog/microservices-correlation-id)

---

### 11. Improve Type Hints
**Location:** [event_store.py:60](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py#L60), [__init__.py:19](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/__init__.py#L19)

**Problem:** Missing type hints reduce IDE support and type checking.

**Fix:**
```python
from typing import Callable, Any, TypeVar
from pathlib import Path

T = TypeVar('T')

def replay_events(self, file_path: str | Path) -> None:
    # ...

def events() -> EventStore:
    # ...
```

**Resources:**
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [mypy Documentation](https://mypy.readthedocs.io/)

---

### 12. Better API Naming
**Location:** [event_store.py:13](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py#L13), [__init__.py:9, 19](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/__init__.py)

**Problem:** Inconsistent naming conventions.

**Suggestions:**
- `add_subscriber` → `subscribe` (shorter, common pattern)
- `events()` → `get_event_store()` (clearer intent)
- `init_event_extension` → `init_events` (consistent with `events()`)

**Resources:**
- [PEP 8 Naming Conventions](https://peps.python.org/pep-0008/#naming-conventions)
- [API Design Best Practices](https://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api)

---

## 💡 Low Priority (Nice to Have)

### 13. Async Support
**Problem:** Synchronous handlers block event processing.

**Fix:**
```python
import asyncio

async def emit_async(self, event: Any) -> None:
    # ... persist event ...
    
    tasks = [handler(event) for handler in handlers]
    await asyncio.gather(*tasks, return_exceptions=True)
```

**Resources:**
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Async Patterns](https://fastapi.tiangolo.com/async/)

---

### 14. Event Filtering
**Problem:** Subscribers receive all events of a type, no fine-grained control.

**Fix:**
```python
def subscribe(
    self, 
    handler: Callable[[Any], None],
    filter_fn: Callable[[Any], bool] | None = None
) -> None:
    # Store filter with handler
    self._subscribers[event_type].append((handler, filter_fn))

def emit(self, event: Any) -> None:
    for handler, filter_fn in handlers:
        if filter_fn is None or filter_fn(event):
            handler(event)
```

**Resources:**
- [Publish-Subscribe Pattern](https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern)

---

### 15. Batch Operations
**Problem:** Emitting many events = many file writes.

**Fix:**
```python
def emit_many(self, events: list[Any]) -> None:
    # Batch write to file
    lines = [self._serialize(event) for event in events]
    self._events_file.writelines(lines)
    
    # Notify subscribers
    for event in events:
        self._notify_subscribers(event)
```

---

### 16. Documentation
**Problem:** No usage examples or comprehensive docstrings.

**Fix:** Create `doc/event_store_usage.md` with examples:
```python
# Example: Subscribe to events
from flaskr.events import events

def on_user_created(event: UserCreatedEvent):
    send_welcome_email(event.user_id)

events().subscribe(on_user_created)

# Example: Emit events
events().emit(UserCreatedEvent(user_id=123))
```

**Resources:**
- [Writing Great Documentation](https://www.writethedocs.org/guide/)
- [Python Docstring Conventions](https://peps.python.org/pep-0257/)

---

## Summary

| Priority | Count | Action Required |
|----------|-------|-----------------|
| 🔴 Critical | 4 | Fix before production |
| ⚠️ High | 4 | Fix in next sprint |
| 📝 Medium | 4 | Quality improvements |
| 💡 Low | 3 | Future enhancements |

**Recommended Fix Order:**
1. Make file path configurable (#2)
2. Add proper file cleanup (#1)
3. Fix replay behavior (#3)
4. Add error handling (#4)
5. Add thread safety (#5)
6. Implement unsubscribe (#6)
