REQUIREMENT
    ↓
ACTORS
    ↓
RESOURCES
    ↓
RELATIONSHIPS
    ↓
USE CASES
    ↓
AUTHORIZATION / SCOPE
    ↓
INVARIANTS
    ↓
STATE / TRANSITIONS
    ↓
FAILURE + CONCURRENCY
    ↓
API CONTRACT
    ↓
IMPLEMENTATION

**Domain:** A platform where users create events and other users reserve seats to attend them.
**Event fields:** title, description, city, event date/time, capacity (max seats), organizer, created_at. Any others are your design decision.

**Validation rules (requirements, not hints):**

- Capacity must be a positive number
- Event date cannot be in the past at creation time
- Title required; description optional
**Behavioral rules for #9 (state as requirements — the "how" is yours):**

- A user cannot reserve the same event twice — the API must reject duplicates, and the rejection must be a 4xx with a readable error. **You choose the exact status code — document why.**
- A reservation cannot be created for an event with no seats left — rejected, 4xx, readable error
- Reserving a non-existent event → 404
- Reserving a past event → rejected. You decide the status code and document it
- **Open design decision:** can the organizer reserve their own event? Decide, document, implement consistently
- **Open design decision:** when a reservation is cancelled, does the seat become available again? Prove your answer with a Postman test
## Actors

- so it's a system where a user can Create an event, and other users can book the event

**Domain** here is Event Booking system

**Actors** - User - reserving seats for events | creating events
**Resource** - event, reservations (booking)
**Relation** - 
- here relation is between who is creating the event (organizer) and who is reserving seats (normal user)
- (requirements don't mention named - users. so assuming it's organizers and normal users)
- an event(resource) (booked by an organizer) can have many users.
	- event is a single resource which will have many reservations(resource) by users (actors)
	- a user (organizer) can create many events. 
	- a user (normal) can be part of many reservations 
**Ownership**
- user owns reservation (resource) (booked reservation)
- user owns event (booked events by user) 
- user (organizer) owns it's own details
- same goes for a normal user. 

**Use-cases**
 - User can create / update / delete events
 - User can create / delete / update (optional/ complex) reservations

*Open ended questions & Assumptions*
- can user here edit the dates for the event? if it has a future date available (complex)
- affect of deletion/ update by organizer on users who have booked/reserved seats
- can a user be both - organizer and a user?
- while booking can a user (organizer) book reservation for other events? 
- also here date altercations (or updates) play important role

**Authorization  / Scope**
- a normal user can see the events available, seats booked (reservations placed), past booked seats
- an organizer can see it's own events, number of users booked seats. 
- an organizer can only see more details (authorized)
- an event is visible to any user/non-user
- unauthorized / other users are not allowed to update event other than organizer

*Open ended questions , Assumptions*
- what happens to the old events (once they are completed / past the date)

**States**
as of now going with
- events are booked / cancelled / rescheduled(optional) 
- a event should exist to make the actual altercation . 

**Validations**
- event should exist
- event's seats should be positive / 
- validate if seats are available before booking 
- unauthorized user cannot reserve
- check if already reserved by other user
- events can / cannot be altered once created?
.. 


**Invariants**

*for events*
- events cannot be cancelled after it's finished
- a user cannot book event before current date
- organizer cannot reserve in it's own event
- what happens to the old events
- can seats be altered? once created?

*booking/reservations*
- 2 users cannot reserve same seats
- reservation is not allowed once max capacity is reached for an event
- can a user be part of 2 reservations on the same data/time
- how is user's detail affected for reservations in case of update in events
- if max seats are reached , should user see that ? 
- what happens to the seat if user is either deleted / cancels the seat/ how is it managed?

**Failures**
*hidden consideration of payment is not taken into account*
- unavailable seats are being booked
- 2 users getting same seats
- update on event change not reaching the user's booked data.
- being able to book an event which is already finished or deleted.
- external failures (DB / timeout / network)


*other assumptions/ questions*
- how much access does an unauthorized user have on events
- what happen to a seat if user is deleted or an event if organizer deletes the event
- what happens if two users try to reserve the last seat at the same moment?
