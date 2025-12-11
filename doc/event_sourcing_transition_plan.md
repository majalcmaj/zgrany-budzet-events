# Event Sourcing Transition Plan

The current system uses a **State-Oriented Persistence** model. You store the current state of the world (e.g., `status = "planning_in_progress"`, list of expenses) in memory or a database. When a change happens, you overwrite the old value. You lose the history of *how* you got there.

**Event Sourcing** flips this: you persist the **actions (events)** that happened, and the current state is just a calculation (a "projection") derived by replaying those events.

Here is the high-level path to migrate your specific Budget Planning application.

## 1. The Core Concept Shift

Instead of:
> "Update status to IN_PROGRESS"

You save:
> "Event: PlanningStarted happened at 12:00 by Chief"

## 2. Domain Events
You would need to define immutable events that represent every significant change in your system. Based on your current code, these would likely be:

**Planning Lifecycle Events:**
*   `PlanningCycleInitialized` (created for a specific year)
*   `DeadlineSet(date)`
*   `PlanningStarted`
*   `PlanningSubmittedToMinister`
*   `CorrectionRequested(comment)`
*   `PlanningApproved`
*   `PlanningReopened`

**Expense Events:**
*   `ExpenseAdded(data...)`
*   `ExpenseModified(expense_id, changes...)`
*   `ExpenseDeleted(expense_id)`
*   `OfficeExpensesSubmitted(office_name)`
*   `OfficeExpensesReopened(office_name)`

## 3. Architecture Components

To implement this, you would introduce three main moving parts:

### A. The Event Store
A single database table (e.g., `events`) that stores every event in order.
*   **Schema:** `id | stream_id | event_type | data (JSON) | created_at | version`
*   **Immutability:** You strictly *insert* only. You never update or delete rows here.
*   **Stream ID:** Examples: `planning_2025` (for the overall process) or `expense_123` (if you track expenses individually).

### B. The Aggregate (Write Model)
The "Brain" that decides if a command is valid.
*   It loads past events for a specific ID (e.g., the Planning Cycle).
*   It replays them to rebuild the current internal state in memory.
*   It checks business rules (e.g., *"Can I submit to Minister?"* -> *Only if state is currently IN_PROGRESS*).
*   If valid, it produces a **new event** (e.g., `PlanningSubmitted`) and saves it to the store.

### C. Projections (Read Models)
Since querying a list of thousands of events to show a dashboard is slow, you create "Projections".
*   These are tables (like you currently have) optimized purely for reading.
*   **Event Handler:** Listens for `ExpenseAdded`, and does `INSERT INTO expenses_read_table ...`.
*   **Event Handler:** Listens for `PlanningApproved`, and does `UPDATE dashboard_stats SET status = 'DONE'`.
*   You can wipe these tables and rebuild them from scratch by replaying the Event Store at any time.

## 4. Migration Path (High Level)

1.  **Stop changing state directly**: In `flaskr/planning/state.py`, instead of `self.status = ...`, you would change methods to `self.record_event(PlanningStarted())`.
2.  **Create the Event Store**: Add the table to SQLite/Postgres.
3.  **Refactor `PlanningState`**:
    *   Add an `apply(event)` method that updates the variables based on an event.
    *   Update methods like `start_planning()` to creating an event, appending it to the store, and then calling `apply()`.
4.  **Refactor Global `EXPENSES`**: The global in-memory dict would be replaced by a Projection that listens to events or is rebuilt on startup.

## 5. Tradeoffs

| Feature | Pros (Why do it?) | Cons (Why hesitate?) |
| :--- | :--- | :--- |
| **Audit Trail** | You get a perfect history of *who* did *what* and *when*. "Who changed this budget item?" is a trivial query. | **Complexity**: It is significantly harder to write simple CRUD features. You need more boilerplate (Events, Commands, Handlers). |
| **Debugging** | **Time Travel**: You can copy the production event log to your machine and "replay" it to see exactly how a bug occurred. | **Version Management**: If you change the structure of an Event (e.g., rename a field), you must handle "upcasting" old events forever. |
| **Scalability** | You can scale writes (Event Store) and reads (Projections) independently. | **Eventual Consistency**: There is often a tiny delay between "Saving" and "Seeing it on the dashboard". |
| **Simplicity** | Reading data is super fast because Read Models are flat tables tailored exactly for the UI. | **Storage**: The event log grows indefinitely. You never delete data, even if an item is "deleted" in the app. |

## Recommendation
For **zgrany-budget-events**:
Since this seems to be a specific workflow with distinct states and multiple actors (Chief, Minister, Offices) modifying a shared plan, **Event Sourcing is a very natural fit**. The complexity of the "Workflow" (transitions, approvals, corrections) is exactly where Event Sourcing shines over CRUD.

However, the current setup is simple (in-memory/simple DB). Migrating adds infrastructure weight. You might consider a **"Light" Event Sourcing** approach:
*   Keep the current `db.Model` tables for reading.
*   But strictly ensure every mutation *also* logs an immutable "Audit Record" to a table.
*   You don't rebuild state from events, but you get the Audit logs. This describes 80% of the value for 20% of the effort.
