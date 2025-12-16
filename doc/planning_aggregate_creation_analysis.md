
# Analysis of Planning and Expense Aggregate Creation Options

## Problem Statement
The goal is to instantiate a `PlanningAggregate` and multiple associated `ExpenseAggregate`s (one per office) when a `planning_scheduled` event occurs. The challenge is to choose an implementation that ensures consistency, decouples components appropriately, and allows for easy reconstitution of aggregates (replayability) from the event store.

## Options Summary

| Option | Description | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **1. Independent Listeners** | A listener creates `PlanningAggregate`. A separate listener creates `ExpenseAggregate`s. both react to `PlanningScheduled`. | • Simple to implement initially.<br>• Decoupled logic. | • **Replay Difficulty:** `ExpenseAggregate` depends on an event (`PlanningScheduled`) that resides in a different stream (e.g., `planning_scheduled`). Rebuilding an expense aggregate requires correctly replaying that external stream.<br>• Implicit dependency on external stream presence. |
| **2. Process Manager / Translator (Recommended)** | `PlanningScheduled` triggers a listener (Process Manager) that emits explicit creation events (e.g., `ExpenseScheduled`) into the specific `ExpenseAggregate` streams. | • **Self-Contained Streams:** `ExpenseAggregate` stream contains its own creation event (`ExpenseScheduled`). Replaying just `expenses-{id}` fully rebuilds the aggregate.<br>• **Explicit Lifecycle:** Creation is an explicit event in the aggregate's history.<br>• **Queryable:** Can easily query `ExpenseScheduled` events to find all aggregates. | • Slightly more boilerplate (new event type, extra listener step).<br>• Eventual consistency (standard in ES). |
| **3. Coupled Creation** | The command that triggers `PlanningScheduled` also triggers `ExpenseScheduled` events, OR the `PlanningAggregate` emits them. | • potentially atomic creation (if supported). | • **High Coupling:** The command handler or `PlanningAggregate` must know about `ExpenseAggregate` logic/offices.<br>• Violates aggregate boundaries if one aggregate creates another directly. |

## Deep Dive

### Option 1: Independent Listeners (Current Approach)
Currently, `PlanningAggregate` and `ExpenseAggregate` both subscribe to the `planning_scheduled` stream.
- **Mechanism:** `EventStore` notifies both listeners when `PlanningScheduled` is emitted.
- **The Issue:** `ExpenseAggregate` resides conceptually in a stream like `expenses-{year}-{office}`. However, its "birth" event `PlanningScheduled` is in the `planning_scheduled` stream.
    - To reload `ExpenseAggregate` from storage, you cannot simply load `expenses-{year}-{office}` because it would be empty (or missing the creation event).
    - You would have to implement a complex loading strategy that knows to look at `planning_scheduled` first.

### Option 2: Process Manager / Translator (Recommended)
This pattern uses a "Process Manager" (or simply a policy/listener) to translate the `PlanningScheduled` event into specific commands or events for the `ExpenseAggregate`s.
- **Mechanism:**
    1. `PlanningScheduled` event emitted to `planning_scheduled` stream.
    2. A listener (e.g., `PlanningProcessManager`) receives this.
    3. The listener iterates over offices and emits `ExpenseScheduled` (or `ExpenseAggregateCreated`) specifically to the target streams `expenses-{year}-{office}`.
- **Benefits:**
    - **Stream Autonomy:** The `expenses-{year}-{office}` stream now starts with `ExpenseScheduled`. It is self-sufficient. Loading the aggregate is just `repo.load(stream_id)`.
    - **Traceability:** You can see exactly when the expense aggregate was created in its own history.

### Implementation Sketch for Option 2

1.  **Define Event:** `ExpenseScheduled(stream_id=..., year=..., office=...)`
2.  **Listener:**
    ```python
    def planning_scheduled_policy(event: PlanningScheduled) -> None:
        events_to_emit = []
        for office in event.offices:
            stream_id = f"expenses-{event.planning_year}-{office}"
            events_to_emit.append(
                ExpenseScheduled(stream_id=stream_id, ...)
            )
        events().emit(events_to_emit)
    ```
3.  **ExpenseAggregate:** handles `ExpenseScheduled` to initialize its state.

## Recommendation
**Option 2** is the robust choice for a production-grade Event Sourced system. It solves the replayability/loading problem identified in Option 1 by ensuring that every aggregate's stream is self-contained and strictly ordered, starting with its own creation event.
