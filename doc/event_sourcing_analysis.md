# Event Sourcing Analysis & Roadmap

## Executive Summary

The current implementation is **NOT proper event sourcing** but rather a **hybrid approach** that combines:
- ✅ Event-driven architecture (pub/sub pattern)
- ✅ Event persistence (append-only log)
- ❌ In-memory state management (not event-sourced)
- ❌ Missing aggregate boundaries
- ❌ No event versioning or schema evolution
- ❌ No proper event replay for state reconstruction

**Current State**: Event notification system with persistence  
**Target State**: Full event sourcing with CQRS pattern

---

## Current Implementation Review

### What Works Well ✅

#### 1. Event Store Infrastructure
- **File**: [event_store.py](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_store.py)
- Implements pub/sub pattern with type-based routing
- Thread-safe event emission and subscription
- Clean separation between `EventStore` protocol and implementation

#### 2. Event Persistence
- **File**: [event_repository.py](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_repository.py)
- Append-only JSONL format for events
- Captures event type, module, and payload
- Immutable event log (no updates/deletes)

#### 3. Event Replay Capability
- **File**: [replay_wrapper.py](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/replay_wrapper.py)
- Can replay events from file
- Prevents duplicate persistence during replay

---

## Critical Issues ❌

### 1. **State is Not Event-Sourced**

**Problem**: State is managed in-memory, not derived from events.

**Evidence** ([state.py](file:///home/mc/workspace/zgrany-budget-events/flaskr/planning/state.py)):
```python
# Lines 14-15: Global mutable state
EXPENSES: dict[str, list[Expense]] = {office: [] for office in OFFICES}
EXPENSES_CLOSED = {office: False for office in OFFICES}

# Lines 49-52: Direct state initialization
self.deadline: str | None = None
self.status = PlanningStatus.NOT_STARTED
self.correction_comment: str | None = None
self.planning_year = 2025
```

**Impact**: 
- State is lost on application restart
- Cannot reconstruct state from events
- No audit trail for state changes
- Impossible to debug historical states

---

### 2. **Missing Aggregate Root Pattern**

**Problem**: No clear aggregate boundaries or consistency guarantees.

**Evidence**:
- `EXPENSES` is a global dictionary modified directly ([expenses/__init__.py:89](file:///home/mc/workspace/zgrany-budget-events/flaskr/planning/expenses/__init__.py#L89))
- `EXPENSES_CLOSED` modified as side effect in event handlers ([state.py:78-79](file:///home/mc/workspace/zgrany-budget-events/flaskr/planning/state.py#L78-L79))
- No transactional boundaries around state changes

**Impact**:
- Race conditions possible
- Inconsistent state across aggregates
- Difficult to enforce business rules

---

### 3. **Events Don't Capture All State Changes**

**Problem**: Critical state mutations happen outside events.

**Evidence** ([expenses/__init__.py](file:///home/mc/workspace/zgrany-budget-events/flaskr/planning/expenses/__init__.py)):
```python
# Line 89: Direct mutation, no event
EXPENSES[session["role"]].append(expense)

# Line 139: Direct mutation, no event  
EXPENSES_CLOSED[session["role"]] = True
```

**Impact**:
- Incomplete event log
- Cannot replay to current state
- Lost business context

---

### 4. **No Event Versioning**

**Problem**: Events lack version information for schema evolution.

**Evidence** ([event_repository.py:31-37](file:///home/mc/workspace/zgrany-budget-events/flaskr/events/event_repository.py#L31-L37)):
```python
event_json = json.dumps({
    "module": event_type.__module__,
    "type": event_type.__name__,
    "payload": payload,
})
# Missing: version, timestamp, aggregate_id, causation_id, correlation_id
```

**Impact**:
- Cannot evolve event schemas safely
- Difficult to migrate old events
- No temporal queries

---

### 5. **Side Effects in Event Handlers**

**Problem**: Event handlers modify global state directly.

**Evidence** ([state.py:77-79](file:///home/mc/workspace/zgrany-budget-events/flaskr/planning/state.py#L77-L79)):
```python
def _handle_planning_started(self, event: _PlanningStartedEvent) -> None:
    self.deadline = event.deadline
    self.status = PlanningStatus.IN_PROGRESS
    # Side effect: Reset office approvals - should be refactored?
    for office in EXPENSES_CLOSED:
        EXPENSES_CLOSED[office] = False
```

**Impact**:
- Violates single responsibility
- Hidden dependencies
- Difficult to test

---

### 6. **No Aggregate Identity**

**Problem**: Events not associated with specific aggregate instances.

**Evidence**:
- Single global `planning_state` instance ([state.py:138](file:///home/mc/workspace/zgrany-budget-events/flaskr/planning/state.py#L138))
- No aggregate ID in events
- Cannot support multiple planning cycles

**Impact**:
- Cannot scale to multiple aggregates
- No multi-tenancy support
- Difficult to partition data

---

## Roadmap to Proper Event Sourcing

### Priority 1: Critical Foundation (Must Have)

#### 1.1 Introduce Aggregate Root Pattern
**Effort**: High | **Impact**: Critical | **Risk**: High

**Tasks**:
- [ ] Create `PlanningAggregate` class with unique ID
- [ ] Move all state into aggregate
- [ ] Implement `apply()` method for event application
- [ ] Add `uncommitted_events` collection
- [ ] Implement `mark_events_as_committed()`

**References**:
- [Aggregate Pattern - Martin Fowler](https://martinfowler.com/bliki/DDD_Aggregate.html)
- [Event Sourcing - Greg Young](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)

**Example**:
```python
class PlanningAggregate:
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self._uncommitted_events: list[Any] = []
        # State
        self.deadline: str | None = None
        self.status = PlanningStatus.NOT_STARTED
        
    def start_planning(self, deadline: str) -> None:
        # Validate
        if self.status != PlanningStatus.NOT_STARTED:
            raise ValueError(f"Cannot start from {self.status}")
        # Emit event
        event = PlanningStartedEvent(
            aggregate_id=self.aggregate_id,
            deadline=deadline
        )
        self._apply_event(event)
        self._uncommitted_events.append(event)
    
    def _apply_event(self, event: Any) -> None:
        # Apply to state
        if isinstance(event, PlanningStartedEvent):
            self.deadline = event.deadline
            self.status = PlanningStatus.IN_PROGRESS
            self.version += 1
```

---

#### 1.2 Implement Event Metadata
**Effort**: Medium | **Impact**: Critical | **Risk**: Low

**Tasks**:
- [ ] Add `BaseEvent` class with metadata
- [ ] Include: `event_id`, `aggregate_id`, `aggregate_type`, `version`, `timestamp`
- [ ] Add: `causation_id`, `correlation_id` for tracing
- [ ] Update event serialization

**References**:
- [Event Metadata - Eventstore](https://developers.eventstore.com/server/v21.10/streams.html#event-metadata)
- [Event Versioning - Oskar Dudycz](https://event-driven.io/en/simple_events_versioning_with_event_sourcing/)

**Example**:
```python
@dataclass
class BaseEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    aggregate_id: str
    aggregate_type: str
    version: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    causation_id: str | None = None
    correlation_id: str | None = None

@dataclass
class PlanningStartedEvent(BaseEvent):
    deadline: str
```

---

#### 1.3 Create Repository with Event Sourcing
**Effort**: High | **Impact**: Critical | **Risk**: Medium

**Tasks**:
- [ ] Create `AggregateRepository` class
- [ ] Implement `save(aggregate)` - persist uncommitted events
- [ ] Implement `load(aggregate_id)` - replay events to rebuild state
- [ ] Add optimistic concurrency control (version checking)
- [ ] Implement event stream per aggregate

**References**:
- [Repository Pattern - Martin Fowler](https://martinfowler.com/eaaCatalog/repository.html)
- [Optimistic Concurrency - Microsoft](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing#optimistic-concurrency)

**Example**:
```python
class AggregateRepository:
    def save(self, aggregate: PlanningAggregate) -> None:
        events = aggregate.get_uncommitted_events()
        expected_version = aggregate.version - len(events)
        
        # Optimistic concurrency check
        current_version = self._get_current_version(aggregate.aggregate_id)
        if current_version != expected_version:
            raise ConcurrencyException()
        
        # Persist events
        for event in events:
            self.event_store.append(event)
        
        aggregate.mark_events_as_committed()
    
    def load(self, aggregate_id: str) -> PlanningAggregate:
        events = self.event_store.get_events(aggregate_id)
        aggregate = PlanningAggregate(aggregate_id)
        for event in events:
            aggregate._apply_event(event)
        return aggregate
```

---

### Priority 2: Essential Features (Should Have)

#### 2.1 Separate Expenses into Own Aggregate
**Effort**: High | **Impact**: High | **Risk**: Medium

**Tasks**:
- [ ] Create `OfficeExpensesAggregate` class
- [ ] Define events: `ExpenseAddedEvent`, `ExpensesSubmittedEvent`, `ExpensesReopenedEvent`
- [ ] Move `EXPENSES` and `EXPENSES_CLOSED` into aggregate state
- [ ] Update UI to work with new aggregate

**Rationale**: 
- Each office's expenses are a separate consistency boundary
- Enables parallel processing
- Better scalability

---

#### 2.2 Implement Event Versioning
**Effort**: Medium | **Impact**: High | **Risk**: Low

**Tasks**:
- [ ] Add `event_version` field to events
- [ ] Create event upcasters for schema migration
- [ ] Implement version registry
- [ ] Add tests for version compatibility

**References**:
- [Versioning in Event Sourcing - Greg Young](https://leanpub.com/esversioning)
- [Event Versioning Patterns - Oskar Dudycz](https://event-driven.io/en/how_to_do_event_versioning/)

**Example**:
```python
class EventUpcaster:
    def upcast(self, event_data: dict) -> dict:
        version = event_data.get("event_version", 1)
        
        if version == 1:
            # Migrate v1 to v2
            event_data["new_field"] = "default_value"
            event_data["event_version"] = 2
        
        return event_data
```

---

#### 2.3 Add Snapshots for Performance
**Effort**: Medium | **Impact**: Medium | **Risk**: Low

**Tasks**:
- [ ] Implement snapshot storage
- [ ] Create snapshots every N events
- [ ] Load from snapshot + replay recent events
- [ ] Add snapshot cleanup strategy

**References**:
- [Snapshots - Microsoft](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing#snapshots)
- [Snapshot Strategy - Eventstore](https://developers.eventstore.com/clients/grpc/appending-events/#handling-concurrency)

**Rationale**: 
- Improves load performance for long-lived aggregates
- Reduces replay time

---

#### 2.4 Linking Aggregates: Planning & Office Expenses
**Effort**: Medium | **Impact**: High | **Risk**: Medium

**Problem**: How to coordinate between `PlanningAggregate` and multiple `OfficeExpensesAggregate` instances while maintaining aggregate boundaries?

**Solution**: Use a combination of **Aggregate References** + **Domain Events** + **Application Services**.

##### Pattern 1: Aggregate References (Recommended)

The `PlanningAggregate` stores references to `OfficeExpensesAggregate` IDs, but doesn't directly manage their state.

```python
class PlanningAggregate:
    def __init__(self, aggregate_id: str, planning_year: int):
        self.aggregate_id = aggregate_id  # e.g., "planning-2025"
        self.planning_year = planning_year
        self.status = PlanningStatus.NOT_STARTED
        self.deadline: str | None = None
        
        # Reference to child aggregates (not their state!)
        self.office_expense_ids: dict[str, str] = {}
        # e.g., {"finance": "expenses-2025-finance", "hr": "expenses-2025-hr"}
        
    def start_planning(self, deadline: str, offices: list[str]) -> None:
        if self.status != PlanningStatus.NOT_STARTED:
            raise ValueError(f"Cannot start from {self.status}")
        
        event = PlanningStartedEvent(
            aggregate_id=self.aggregate_id,
            version=self.version + 1,
            deadline=deadline,
            office_ids=offices,
            timestamp=datetime.utcnow()
        )
        self._apply_event(event)
        self._uncommitted_events.append(event)
    
    def _apply_event(self, event: Any) -> None:
        if isinstance(event, PlanningStartedEvent):
            self.deadline = event.deadline
            self.status = PlanningStatus.IN_PROGRESS
            # Store references to office expense aggregates
            for office in event.office_ids:
                expense_id = f"expenses-{self.planning_year}-{office}"
                self.office_expense_ids[office] = expense_id
            self.version += 1


class OfficeExpensesAggregate:
    def __init__(self, aggregate_id: str, office: str, planning_id: str):
        self.aggregate_id = aggregate_id  # e.g., "expenses-2025-finance"
        self.office = office
        self.planning_id = planning_id  # Reference back to parent
        self.expenses: list[Expense] = []
        self.is_submitted = False
        
    def add_expense(self, expense: Expense) -> None:
        if self.is_submitted:
            raise ValueError("Cannot add expense after submission")
        
        event = ExpenseAddedEvent(
            aggregate_id=self.aggregate_id,
            version=self.version + 1,
            expense=expense
        )
        self._apply_event(event)
        self._uncommitted_events.append(event)
```

##### Pattern 2: Application Service Coordination

Use an application service to coordinate operations across multiple aggregates.

```python
class PlanningApplicationService:
    def __init__(
        self,
        planning_repo: AggregateRepository,
        expenses_repo: AggregateRepository,
        event_store: EventStore
    ):
        self.planning_repo = planning_repo
        self.expenses_repo = expenses_repo
        self.event_store = event_store
    
    def start_planning(
        self, 
        planning_year: int, 
        deadline: str, 
        offices: list[str]
    ) -> None:
        """Coordinates multiple aggregates"""
        planning_id = f"planning-{planning_year}"
        
        # 1. Start planning aggregate
        planning = PlanningAggregate(planning_id, planning_year)
        planning.start_planning(deadline, offices)
        self.planning_repo.save(planning)
        
        # 2. Create office expense aggregates
        for office in offices:
            expense_id = f"expenses-{planning_year}-{office}"
            expenses = OfficeExpensesAggregate(expense_id, office, planning_id)
            expenses.initialize()  # Emits ExpensesInitializedEvent
            self.expenses_repo.save(expenses)
    
    def submit_planning_to_minister(self, planning_id: str) -> None:
        """Validates all offices submitted before allowing submission"""
        # 1. Load planning aggregate
        planning = self.planning_repo.load(planning_id)
        
        # 2. Check all offices have submitted (read from other aggregates)
        for office, expense_id in planning.office_expense_ids.items():
            expenses = self.expenses_repo.load(expense_id)
            if not expenses.is_submitted:
                raise ValueError(f"Office {office} has not submitted expenses")
        
        # 3. Submit planning
        planning.submit_to_minister()
        self.planning_repo.save(planning)
```

##### Pattern 3: Domain Events for Cross-Aggregate Communication

Use domain events to notify other aggregates when something happens.

```python
class PlanningAggregate:
    def request_correction(self, comment: str) -> None:
        if self.status != PlanningStatus.IN_REVIEW:
            raise ValueError("Can only request correction during review")
        
        # Emit event that will be handled by other aggregates
        event = CorrectionRequestedEvent(
            aggregate_id=self.aggregate_id,
            version=self.version + 1,
            comment=comment,
            planning_year=self.planning_year,
        )
        self._apply_event(event)
        self._uncommitted_events.append(event)


# Process Manager handles cross-aggregate coordination
class PlanningProcessManager:
    def __init__(self, expenses_repo: AggregateRepository):
        self.expenses_repo = expenses_repo
    
    def on_correction_requested(self, event: CorrectionRequestedEvent) -> None:
        """When planning requests correction, reopen all office expenses"""
        planning_year = event.planning_year
        
        # Find all office expense aggregates for this planning year
        for office in OFFICES:
            expense_id = f"expenses-{planning_year}-{office}"
            try:
                expenses = self.expenses_repo.load(expense_id)
                
                # Reopen with causation tracking
                expenses.reopen(
                    causation_id=event.event_id,
                    correlation_id=event.correlation_id
                )
                self.expenses_repo.save(expenses)
            except AggregateNotFound:
                pass  # Office not participating


# Wire up in event store initialization
event_store.add_subscriber(process_manager.on_correction_requested)
```

##### Aggregate Structure Diagram

```
PlanningAggregate (planning-2025)
├── aggregate_id: "planning-2025"
├── planning_year: 2025
├── status: IN_PROGRESS
├── deadline: "2025-12-31"
│
├── References (IDs only, not state):
│   ├── office_expense_ids["finance"] → "expenses-2025-finance"
│   ├── office_expense_ids["hr"] → "expenses-2025-hr"
│   └── office_expense_ids["it"] → "expenses-2025-it"
│
└── Events:
    ├── PlanningStartedEvent
    ├── PlanningSubmittedEvent
    └── CorrectionRequestedEvent ← Published to event store

OfficeExpensesAggregate (expenses-2025-finance)
├── aggregate_id: "expenses-2025-finance"
├── office: "finance"
├── planning_id: "planning-2025" ← Reference back to parent
├── expenses: [Expense(...), Expense(...)]
├── is_submitted: false
│
└── Events:
    ├── ExpensesInitializedEvent
    ├── ExpenseAddedEvent
    ├── ExpensesSubmittedEvent
    └── ExpensesReopenedEvent
        ├── causation_id: <CorrectionRequestedEvent.event_id>
        └── correlation_id: "workflow-123"
```

##### Event Flow Example: Minister Requests Correction

```python
# 1. Minister requests correction
planning = planning_repo.load("planning-2025")
planning.request_correction("Please revise budget")
planning_repo.save(planning)
# → Emits CorrectionRequestedEvent with correlation_id="workflow-123"

# 2. Event store publishes event to subscribers
event_store.emit(CorrectionRequestedEvent(
    event_id="evt-001",
    aggregate_id="planning-2025",
    planning_year=2025,
    correlation_id="workflow-123",
    ...
))

# 3. Process manager reacts (subscribed to event store)
@event_store.subscribe
def on_correction_requested(event: CorrectionRequestedEvent):
    for office in OFFICES:
        expense_id = f"expenses-{event.planning_year}-{office}"
        expenses = expenses_repo.load(expense_id)
        
        # Reopen with causation tracking
        expenses.reopen(
            causation_id=event.event_id,  # "evt-001"
            correlation_id=event.correlation_id  # "workflow-123"
        )
        expenses_repo.save(expenses)
        # → Emits ExpensesReopenedEvent for each office

# 4. Result: All office expenses reopened, full audit trail maintained
```

##### Querying Across Aggregates

```python
def get_planning_summary(planning_id: str) -> dict:
    """Get planning with all office expenses (read model)"""
    planning = planning_repo.load(planning_id)
    
    offices = {}
    for office, expense_id in planning.office_expense_ids.items():
        expenses = expenses_repo.load(expense_id)
        offices[office] = {
            "expenses": expenses.expenses,
            "total": sum(e.financial_needs for e in expenses.expenses),
            "is_submitted": expenses.is_submitted
        }
    
    return {
        "planning_id": planning.aggregate_id,
        "status": planning.status,
        "deadline": planning.deadline,
        "offices": offices,
        "grand_total": sum(o["total"] for o in offices.values())
    }
```

##### Key Design Principles

1. **Aggregate Independence**: Each aggregate can be loaded/saved independently
2. **Eventual Consistency**: Office expenses react to planning events asynchronously
3. **Clear Boundaries**: Planning doesn't modify office expenses directly
4. **Traceability**: `causation_id` and `correlation_id` link related events
5. **Loose Coupling**: Aggregates communicate via events, not direct calls

##### Benefits

- ✅ **Scalability**: Each office's expenses can be processed in parallel
- ✅ **Testability**: Each aggregate can be tested in isolation
- ✅ **Maintainability**: Clear separation of concerns
- ✅ **Audit Trail**: Full history of why things happened (causation)
- ✅ **Flexibility**: Easy to add new office types or workflows

**References**:
- [Aggregate Design - Vaughn Vernon](https://www.dddcommunity.org/wp-content/uploads/files/pdf_articles/Vernon_2011_1.pdf)
- [Process Manager Pattern - Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html)

---

### Priority 3: Advanced Features (Nice to Have)

#### 3.1 Implement CQRS Pattern
**Effort**: High | **Impact**: High | **Risk**: Medium

**Tasks**:
- [ ] Separate read models from write models
- [ ] Create projections for queries
- [ ] Implement eventual consistency
- [ ] Add projection rebuilding capability

**References**:
- [CQRS - Martin Fowler](https://martinfowler.com/bliki/CQRS.html)
- [CQRS Journey - Microsoft](https://learn.microsoft.com/en-us/previous-versions/msp-n-p/jj554200(v=pandp.10))

---

#### 3.2 Add Process Managers/Sagas
**Effort**: High | **Impact**: Medium | **Risk**: High

**Tasks**:
- [ ] Implement process manager for multi-aggregate workflows
- [ ] Handle compensation logic
- [ ] Add timeout handling
- [ ] Implement idempotency

**References**:
- [Process Manager - Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html)
- [Sagas - Chris Richardson](https://microservices.io/patterns/data/saga.html)

---

#### 3.3 Event Store Database
**Effort**: Very High | **Impact**: High | **Risk**: High

**Tasks**:
- [ ] Migrate from JSONL to proper event store (EventStoreDB, PostgreSQL)
- [ ] Implement event streams
- [ ] Add projections support
- [ ] Enable subscriptions and catch-up

**References**:
- [EventStoreDB](https://www.eventstore.com/)
- [Marten for .NET](https://martendb.io/) (concept reference)
- [PostgreSQL Event Sourcing](https://github.com/oskardudycz/EventSourcing.NetCore)

---

## Implementation Sequence

### Phase 1: Foundation (Weeks 1-3)
1. ✅ Create `BaseEvent` with metadata
2. ✅ Implement `PlanningAggregate` 
3. ✅ Build `AggregateRepository`
4. ✅ Add optimistic concurrency
5. ✅ Update tests

### Phase 2: Migration (Weeks 4-5)
1. ✅ Migrate `PlanningState` to use aggregate
2. ✅ Update all command handlers
3. ✅ Ensure backward compatibility
4. ✅ Deploy with feature flag

### Phase 3: Expansion (Weeks 6-8)
1. ✅ Create `OfficeExpensesAggregate`
2. ✅ Implement event versioning
3. ✅ Add snapshots
4. ✅ Performance testing

### Phase 4: Advanced (Weeks 9-12)
1. ✅ Implement CQRS read models
2. ✅ Add projections
3. ✅ Consider process managers
4. ✅ Evaluate event store database

---

## Key References & Resources

### Books
1. **"Implementing Domain-Driven Design"** - Vaughn Vernon
   - Chapter 8: Aggregates
   - Chapter 9: Modules
   
2. **"Versioning in an Event Sourced System"** - Greg Young
   - [Leanpub](https://leanpub.com/esversioning)

3. **"Domain-Driven Design Distilled"** - Vaughn Vernon
   - Quick reference for DDD patterns

### Articles & Blogs
1. **Martin Fowler's Event Sourcing**
   - [https://martinfowler.com/eaaDev/EventSourcing.html](https://martinfowler.com/eaaDev/EventSourcing.html)

2. **Greg Young's CQRS Documents**
   - [https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)

3. **Oskar Dudycz's Event Sourcing Blog**
   - [https://event-driven.io/en/](https://event-driven.io/en/)
   - Excellent practical examples

4. **Microsoft's Event Sourcing Pattern**
   - [https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)

### Video Courses
1. **"Event Sourcing in Practice"** - Oskar Dudycz
   - [YouTube Playlist](https://www.youtube.com/playlist?list=PLw-VZz_H4iiqUeEBDfGNendS0B3qIk-ps)

2. **"CQRS and Event Sourcing"** - Pluralsight
   - Comprehensive course on both patterns

### Code Examples
1. **EventSourcing.NetCore** - Oskar Dudycz
   - [https://github.com/oskardudycz/EventSourcing.NetCore](https://github.com/oskardudycz/EventSourcing.NetCore)
   - Excellent reference implementation

2. **Axon Framework** (Java)
   - [https://axoniq.io/](https://axoniq.io/)
   - Production-ready framework

---

## Risk Assessment

### High Risk Items
1. **State Migration** - Moving from in-memory to event-sourced state
   - Mitigation: Feature flags, parallel run, gradual rollout
   
2. **Performance Impact** - Event replay overhead
   - Mitigation: Snapshots, caching, performance testing
   
3. **Complexity Increase** - Steeper learning curve
   - Mitigation: Documentation, training, pair programming

### Medium Risk Items
1. **Event Schema Evolution** - Breaking changes in events
   - Mitigation: Versioning strategy, upcasters
   
2. **Debugging Difficulty** - Harder to trace issues
   - Mitigation: Better logging, event visualization tools

---

## Success Metrics

### Technical Metrics
- ✅ 100% state reconstructable from events
- ✅ Zero data loss on restart
- ✅ Event replay time < 1s for typical aggregate
- ✅ All business operations captured as events

### Business Metrics
- ✅ Complete audit trail for compliance
- ✅ Ability to query historical states
- ✅ Support for temporal queries ("what was the state on date X?")
- ✅ Debugging time reduced by 50%

---

## Conclusion

The current implementation has a **solid foundation** with event persistence and pub/sub, but lacks the core characteristics of event sourcing:

**Missing**:
- State derived from events
- Aggregate boundaries
- Event versioning
- Proper replay mechanism

**Path Forward**:
1. Start with Priority 1 items (aggregate pattern, metadata, repository)
2. Migrate incrementally with feature flags
3. Add Priority 2 features (versioning, snapshots)
4. Consider Priority 3 for scale (CQRS, event store DB)

**Estimated Timeline**: 8-12 weeks for full implementation of Priority 1 & 2.

**Recommendation**: Begin with Priority 1.1 (Aggregate Root Pattern) as it unlocks all other improvements.
