# Real-time updates

The product promises that changes propagate "instantly" across tiers: a parent sees an attendance
badge the moment a session ends, a student sees a grade the moment it is saved. That promise is
asserted on seven screens.

## The transport

A single Server-Sent Events stream, scoped to the caller.

```http
GET /api/v1/events
Accept: text/event-stream
```

Events are filtered server-side by who is asking: a parent receives only events concerning linked
children, a student only their own, an instructor only their own courses.

{% hint style="warning" %}
**SSE is a proposal, not a settled decision.** The scope document requires real-time
synchronization but never specifies a mechanism. SSE is recommended here because all seven flows
are one-way, server-to-client and read-only — which is exactly what SSE is for, and it costs
considerably less than a WebSocket layer. Revisit if any flow ever needs client-to-server push.
{% endhint %}

## The propagation contract

Each promise in the wireframes maps to one trigger endpoint and one event type.

| Trigger | Event | Appears on |
|---|---|---|
| `POST /live-sessions/{id}/end` | `attendance.saved` | Parent home badges, child detail |
| `POST /attempts/{id}/finalize` | `quiz.graded` | Student quiz result, child detail |
| `POST /lessons/{id}/publish` | `content.published` | Student lesson view, parent home |
| `POST /assignments/{id}/solution/release` | `content.published` | Student lesson view |
| `POST` or `PATCH /live-sessions` | `schedule.changed` | Student dashboard, parent home |
| `POST /payments` | `fee.paid` | Parent home — clears the overdue badge |
| `POST /fees/{id}/remind` | `notification.created` | Parent home |

Note that "End Session & Save Attendance" is a single endpoint precisely because it is the fan-out
trigger. Saving attendance and completing the session are one atomic action with one event.

## Persistence

The stream is not the record. Anything worth showing later is also written to `NOTIFICATIONS` and
readable from [`GET /notifications`](../reference/notifications.md), so a client that was
disconnected still catches up. Treat the stream as an invalidation hint: on receiving an event,
re-read the affected resource rather than trusting the payload as authoritative state.

## Delivery beyond the app

In-app only. Email and push are out of scope for this version, even though the parent tier is
framed as a mobile app and "Send reminder" implies outbound contact.

## Reference

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/events" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
