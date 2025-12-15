# Event Sourcing Analysis - Round 2

This document builds upon the initial findings in `doc/event_sourcing_analysis.md`. It provides a deeper review based on the current codebase state, identifying the "hybrid" implementation gaps and refining the roadmap.

## Status Check: The "Hybrid" Trap

The initial analysis correctly identified a hybrid approach. The current codebase has moved slightly towards event sourcing with the introduction of `PlanningAggregate` in `flaskr/planning/planning_aggregate.py`, but it has fallen into a dangerous "middle ground" that combines the complexity of event sourcing with the fragility of global state.

### 🔍 Key Findings

#### 1. The "Fake" Aggregate
**Ref:** `doc/event_sourcing_analysis.md` (Section: Critical Issues #1, #2)

While `PlanningAggregate` exists, it violates the core aggregate rule: **self-encapsulation**.

*   **Evidence**: `PlanningAggregate` handlers directly modify global variables `EXPENSES_CLOSED`.
    *   `src`: `flaskr/planning/planning_aggregate.py:207`
    *   **Problem**: You cannot verify the state of `PlanningAggregate` in isolation because its effects leak into the global scope. Replaying events won't restore the global `EXPENSES_CLOSED` state if the application restarts, unless the replay logic explicitly touches those globals (which is fragile).

#### 2. Expenses Bypassing Event Store
**Ref:** `doc/event_sourcing_analysis.md` (Section: Critical Issues #3)

The `expenses` blueprint completely ignores the event sourcing architecture.

*   **Evidence**: `flaskr/planning/expenses/__init__.py:93`
    ```python
    EXPENSES[session["role"]].append(expense)
    ```
*   **Problem**: Adding an expense is a direct list append. No event is emitted (`ExpenseAddedEvent` is missing/unused). This means **expenses are lost on restart** and cannot be reconstructed from the event log. The `ExpenseAggregate` class defined in `planning_aggregate.py` is unused in the actual business logic.

#### 3. Event "Anemia"
**Ref:** `doc/event_sourcing_analysis.md` (Section: Critical Issues #4)

The `Event` base class is too thin.

*   **Evidence**: `flaskr/events/types.py`
    ```python
    @dataclass
    class Event:
        stream_id: str
    ```
*   **Problem**: Missing critical metadata (`id`, `timestamp`, `version`). Without `version`, we cannot implement optimistic concurrency control. Without `timestamp`, we lose business time context.

## 🛑 Corrective Actions (Refined Roadmap)

The original roadmap is still valid, but we need to pivot to fix the "hybrid" leakage immediately.

### Priority 0: Stop the Bleeding (Immediate Fixes)

We must stop writing to global variables from the aggregate.

1.  **Encapsulate Expenses in Aggregate**:
    *   Move `EXPENSES` and `EXPENSES_CLOSED` *inside* `PlanningAggregate` (or properly wire `ExpenseAggregate`).
    *   **Why**: To ensure `planning_aggregate.state` is the single source of truth.

2.  **Wire Expenses to Events**:
    *   Change `add_expense` route to **dispatch a command** (`AddExpenseCommand`) instead of appending to a list.
    *   Handler should emit `ExpenseAddedEvent`.
    *   Apply method should update the internal list.

### Priority 1: Strengthen Foundation

1.  **Upgrade `Event` Base Class**:
    *   Add `event_id`, `timestamp`, `metadata`.
    *   **Why**: Essential for debugging and consistency.

2.  **True Repository Pattern**:
    *   Stop using the global `planning_aggregate = PlanningAggregate()` singleton in `planning_aggregate.py`.
    *   Instantiate `PlanningAggregate` via a repository that loads history from `EventStore`.

## Implementation details for next steps

The path forward involves refactoring `flaskr/planning/expenses/__init__.py` to stop using globals and start using the `PlanningAggregate` (or `ExpenseAggregate`) via commands.

### Proposed Code Structure Change

**Current**:
```python
# flaskr/planning/expenses/__init__.py
EXPENSES[role].append(expense)
```

**Target**:
```python
# flaskr/planning/expenses/__init__.py
command = AddExpenseCommand(role, expense)
planning_service.handle(command)
# Service loads aggregate -> agg.add_expense() -> emits event -> apply() updates state -> repo saves events
```

This effectively implements **Priority 2.1 (Separate Expenses into Own Aggregate)** from the original plan, but does it by first integrating it correctly into the existing flow.
