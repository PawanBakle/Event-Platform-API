# Event Booking System — Design Document

## 1. Domain

An event booking system where users can create events and other users can reserve a place at those events, subject to event capacity and booking rules.

---

# 2. Actors

### User

A system user can:

- Create an event.
    
- Organize events they created.
    
- Reserve an event.
    
- Potentially cancel their reservation, depending on the cancellation design.
    

**Important:** “Organizer” is treated as a relationship to an Event, not as a separate global user type. The same User may organize one event and reserve another event.

---

# 3. Resources

### Primary resources

1. **Event**
    
2. **Reservation**
    

### Supporting resource

3. **User**
    

The main operations of the system are performed on Events and Reservations.

---

# 4. Identity

### Event

Each event requires a unique identifier.

### Reservation

Each reservation requires a unique identifier.

Additionally, the system must enforce uniqueness of the combination:

> `(user, event)`

This prevents the same user from reserving the same event more than once.

### User

Each user has a unique identity used to associate them with events and reservations.

---

# 5. Relationships

```text
User
 ├── organizes ──> Event
 │                    │
 │                    │ 1-to-many
 │                    ▼
 │               Reservation
 │                    ▲
 │                    │
 └── reserves ────────┘
```

More explicitly:

- One User can organize many Events.
    
- Each Event has exactly one Organizer.
    
- One User can create many Reservations.
    
- Each Reservation belongs to exactly one User.
    
- One Event can have many Reservations.
    
- Each Reservation belongs to exactly one Event.
    

Therefore:

```text
User 1 ──── * Event
User 1 ──── * Reservation
Event 1 ──── * Reservation
```

There is also a many-to-many relationship between Users and Events through Reservations:

```text
User * ──── * Event
       through
      Reservation
```

---

# 6. Ownership / Control

Ownership should not be inferred merely from who performs an operation.

### Event

The Event has an **organizer**:

```text
Event.organizer → User
```

The organizer is the user associated with controlling the event, subject to the authorization rules defined below.

### Reservation

A Reservation is associated with the User who made it:

```text
Reservation.user → User
```

Whether that should be treated as formal “ownership” depends on the final cancellation/modification rules.

---

# 7. Explicit Requirements

The assignment explicitly requires:

### Event creation

A user can create an Event.

Event fields:

- `title`
    
- `description`
    
- `city`
    
- `event_datetime`
    
- `capacity`
    
- `organizer`
    
- `created_at`
    

Other fields may be added if necessary.

### Event validation

- `title` is required.
    
- `description` is optional.
    
- `capacity` must be positive.
    
- Event date/time cannot be in the past when the event is created.
    

### Reservation

A user can reserve an Event.

The system must reject:

1. Duplicate reservation by the same user for the same event.
    
2. Reservation when the event has no available capacity.
    
3. Reservation for a non-existent event.
    
4. Reservation for an event that has already passed.
    

---

# 8. Use Cases

## UC1 — Create Event

A User creates an Event and becomes its organizer.

## UC2 — Reserve Event

A User creates a Reservation for an Event.

The system must verify:

- Event exists.
    
- Event has not already passed.
    
- User has not already reserved the Event.
    
- Capacity is still available.
    

## UC3 — View Events

Users may view available events, subject to the final visibility rules.

## UC4 — Manage Own Event

The organizer may potentially modify/manage their own Event.

This is a design decision because the assignment explicitly requires event creation but does not fully define event update/delete behavior.

## UC5 — Cancel Reservation

Cancellation is a possible operation, but the assignment leaves its exact behavior open.

---

# 9. Operations

The system should distinguish domain operations from generic CRUD.

### Event operations

- Create Event
    
- Read Event
    
- Potentially Update Event
    
- Potentially Cancel/Delete Event
    

### Reservation operations

- Create Reservation
    
- Read Reservation
    
- Potentially Cancel Reservation
    

Cancellation should be treated as a domain operation/state transition rather than automatically assuming it means deleting the database record.

---

# 10. Authorization

Authorization should be expressed as:

> **Actor + Operation + Resource + Scope**

Examples:

### Create Event

```text
User + CREATE + Event
```

A user may create an event.

### Update Event

If event modification is allowed:

```text
User + UPDATE + Event
Scope: Event.organizer == request.user
```

Only the organizer of that event can modify it.

### Create Reservation

```text
User + CREATE + Reservation
Scope: requested Event
```

The user may reserve an event if all reservation preconditions and invariants are satisfied.

### Read Event

The final visibility policy must be decided.

Possible design:

```text
Authenticated User + READ + Event
Scope: events visible to users
```

---

# 11. Scope

Scope determines **which instances** a user can access.

For example:

### Organizer

Can access/manage:

```text
Events where Event.organizer == request.user
```

### User's Reservations

Can access:

```text
Reservations where Reservation.user == request.user
```

### Public Event Visibility

If events are publicly visible, users can read events without being their organizer.

This needs to be explicitly decided rather than assumed.

---

# 12. Invariants

These are rules that must remain true regardless of which API endpoint is used.

## Event invariants

1. `capacity > 0`
    
2. Event must have an organizer.
    
3. Event must have a title.
    
4. Event creation cannot accept a past event datetime.
    

## Reservation invariants

1. Reservation must reference an existing User.
    
2. Reservation must reference an existing Event.
    
3. A User cannot have more than one Reservation for the same Event.
    

Formally:

```text
UNIQUE(user, event)
```

## Capacity invariant

For an Event:

```text
active reservations <= event.capacity
```

This must remain true even when multiple users attempt to reserve the final available capacity simultaneously.

---

# 13. Validation

### Event input validation

- Title must be provided.
    
- Capacity must be greater than zero.
    
- Event datetime must not be in the past at creation time.
    

### Reservation validation

Before creating a Reservation:

- Event must exist.
    
- Event must not have already passed.
    
- User must not already have a Reservation for the Event.
    
- Available capacity must exist.
    

Note:

> “Event exists” is primarily a resource lookup/precondition, not an Event validation rule.

---

# 14. Preconditions

Before creating a Reservation:

```text
Event exists
AND
Event has not passed
AND
User has not already reserved Event
AND
available capacity > 0
```

Only after these conditions are satisfied should the reservation be created.

However, the capacity check cannot simply be treated as a normal sequential validation because concurrent requests can invalidate the result between the check and the write.

---

# 15. State

The original design considered event states such as:

```text
Scheduled
Cancelled
Completed
```

Potential Reservation states:

```text
Active
Cancelled
```

### Important distinction

“Rescheduled” is more naturally an **operation/change to the event datetime** than an Event state.

For example:

```text
Scheduled
   |
   | reschedule
   v
Scheduled
```

The state remains Scheduled while the datetime changes.

---

# 16. State Transitions

Potential Event transitions:

```text
Scheduled → Cancelled
Scheduled → Completed
```

Potential Reservation transitions:

```text
Active → Cancelled
```

Invalid transitions should be rejected.

For example:

```text
Completed → Cancelled
```

may be disallowed, depending on the final business rules.

These transitions are design decisions unless explicitly required by the assignment.

---

# 17. Concurrency / Race Conditions

The most important concurrency problem is the **last available capacity**.

Example:

```text
Event capacity = 10
Current reservations = 9
```

Two users simultaneously attempt to reserve the event.

Both requests may initially observe:

```text
available capacity = 1
```

If both then create a Reservation independently:

```text
10 existing reservations
+ User A
+ User B
= 11 reservations
```

This violates:

```text
reservations <= capacity
```

Therefore the implementation must ensure the capacity invariant survives concurrent requests.

This is a database/transaction-level concern, not merely serializer validation.

---

# 18. Failure Modes

### Event failures

- Missing title.
    
- Invalid/non-positive capacity.
    
- Event creation with past datetime.
    
- Attempt to modify an event without authorization.
    
- Attempt to modify a non-existent event.
    

### Reservation failures

- Event does not exist → `404`.
    
- User already reserved event → readable `4xx`.
    
- Event has no capacity → readable `4xx`.
    
- Event has already passed → readable `4xx`.
    
- User is not authorized for the requested operation → appropriate authorization response.
    
- Concurrent reservation attempts exceed capacity → system must prevent the invariant from being violated.
    

### Concurrency failure

Two users attempting to reserve the final available capacity must not result in both reservations succeeding.

Exactly how the losing request is reported is an implementation/API decision, but the system must preserve the capacity invariant.

---

# 19. Response / API Contract

The assignment already provides the API endpoints, so endpoint discovery is not required here.

However, each endpoint should still have a defined contract:

```text
HTTP Method
Path
Authentication requirement
Request body
Actor
Operation
Resource
Authorization
Preconditions
Validation
Success response
Failure responses
Response body
```

Important status-code distinctions:

- `201 Created` — successful resource creation.
    
- `200 OK` — successful retrieval/update where appropriate.
    
- `400 Bad Request` — invalid request/business input where appropriate.
    
- `401 Unauthorized` — authentication is required but the requester is not authenticated.
    
- `403 Forbidden` — authenticated requester lacks permission.
    
- `404 Not Found` — requested resource does not exist.
    

The exact status for duplicate reservation, past-event reservation, and capacity exhaustion should be chosen and documented consistently.

---

# 20. Open Design Decisions

These are not requirements yet. They need an explicit decision before implementation.

### A. Can an organizer reserve their own event?

Possible choices:

- Yes.
    
- No.
    

If No, this becomes a reservation business rule.

### B. Does cancelling a reservation release capacity?

Possible behavior:

```text
Reservation cancelled
→ active reservation count decreases
→ capacity becomes available again
```

If cancellation is supported, this behavior should be explicitly defined.

### C. Can an organizer update an event?

If yes:

- Which fields can change?
    
- Can capacity be reduced below the current number of reservations?
    
- Can event datetime be moved into the past?
    
- What happens to existing reservations?
    

### D. Can an event be deleted/cancelled after reservations exist?

Need to define what happens to existing reservations.

### E. Visibility

Decide whether:

- Events are publicly readable.
    
- Only authenticated users can view them.
    
- Past events remain visible.
    
- Users can see booking counts.
    
- Organizers can see reservation/user details.
    

### F. Reservation cancellation

Decide whether users can cancel their own reservations and whether cancellation is represented by:

```text
status = cancelled
```

or by deleting the reservation.

---

# 21. Assumptions

Unless the assignment specifies otherwise, the following should be treated as explicit assumptions rather than hidden facts:

1. A User may both organize events and reserve events.
    
2. “Organizer” is a relationship between User and Event, not a separate User type.
    
3. One Event has one Organizer.
    
4. One Reservation belongs to one User and one Event.
    
5. A user can reserve an event at most once.
    
6. Capacity represents the maximum number of active reservations.
    
7. There are no individual seat numbers because the requirements specify only total capacity.
    
8. Cancellation behavior is not assumed until explicitly decided.
    
9. Event update/delete behavior is not assumed merely because those operations are technically possible.
    

---

# 22. Design Questions to Resolve Before Coding

Before touching models or database schema, the remaining decisions are:

1. Can the organizer reserve their own event?
    
2. Can users cancel reservations?
    
3. Does cancellation release capacity?
    
4. Can organizers update events?
    
5. Can capacity be reduced below existing reservations?
    
6. Can organizers change an event's date/time?
    
7. Can events be cancelled after reservations exist?
    
8. What happens to existing reservations when an event is cancelled?
    
9. Are events publicly readable?
    
10. Are past events still visible?
    
11. What reservation details can organizers see?
    
12. What happens when two users attempt to reserve the last available capacity simultaneously?
    

---

# 23. Pre-Implementation Checklist

Before writing Django models:

```text
[✓] Actors identified
[✓] Resources identified
[✓] Resource identities identified
[✓] Relationships identified
[✓] Organizer relationship identified
[✓] Use cases identified
[✓] Operations identified
[✓] Authorization/scopes identified
[✓] Core invariants identified
[✓] Validation rules identified
[✓] Preconditions identified
[✓] States/transitions considered
[✓] Failure modes identified
[✓] Concurrency problem identified
[✓] API contract considered
[ ] Open business decisions resolved
[ ] Assumptions explicitly accepted
```

Once the remaining business decisions are resolved, the design can move to:

```text
Domain
    ↓
Database / Model design
    ↓
Database constraints
    ↓
Query/data-access design
    ↓
Serializer/input validation
    ↓
Authorization/permissions
    ↓
Business logic / transactions
    ↓
Views
    ↓
URLs
    ↓
Tests
```

The key principle is:

> **Do not let the Django model or serializer become the first place where the business rules are discovered.**
> 
> The model, constraints, transactions, serializers, permissions, and views should implement decisions that have already been made at the design level.