# Specification status

Every operation carries a status line. This page explains the three labels and lists what is currently blocking what.

## The three labels

{% hint style="success" %}
**✅ Specifiable** — fully backed by the entity-relationship diagram. The request and response shapes are final and implementation can begin.
{% endhint %}

{% hint style="warning" %}
**⚠️ Awaiting a decision** — the data exists, but a behavioural question is open. The shape shown is the recommended reading; confirm it before building, because some of these change the endpoint, not just its semantics.
{% endhint %}

{% hint style="danger" %}
**🚫 Blocked** — depends on an entity that does not exist in the schema. The shape shown is a proposal to be reviewed, not a contract to build against.
{% endhint %}

## By resource group

| Group                                              | ✅ Ready | ⚠️ Decision | 🚫 Blocked |
| -------------------------------------------------- | ------- | ----------- | ---------- |
| [Authentication](../reference-1/authentication.md) | 12      | 0           | 0          |
| [Invites](../reference-1/invites.md)               | 5       | 0           | 0          |
| [Billing](../reference-1/billing.md)               | 2       | 2           | 0          |
| [Subjects](../api/reference/subjects.md)           | 1       | 0           | 0          |
| [Courses](../reference-1/courses.md)               | 5       | 0           | 0          |
| [Chapters](../reference-1/chapters.md)             | 6       | 0           | 0          |
| [Lessons](../reference-1/lessons.md)               | 8       | 0           | 0          |
| [Materials](../reference-1/materials.md)           | 5       | 0           | 0          |
| [Recordings](../reference-1/recordings.md)         | 5       | 0           | 0          |
| [Uploads](../reference-1/uploads.md)               | 0       | 1           | 0          |
| [Assignments](../reference-1/assignments.md)       | 10      | 1           | 0          |
| [Groups](../reference-1/groups.md)                 | 5       | 3           | 0          |
| [Assistants](../reference-1/assistants.md)         | 7       | 0           | 0          |
| [Scheduling](../reference-1/scheduling.md)         | 6       | 1           | 0          |
| [Attendance](../reference-1/attendance.md)         | 5       | 0           | 0          |
| [Quizzes](../reference-1/quizzes.md)               | 10      | 0           | 0          |
| [Quiz attempts](../reference-1/attempts.md)        | 5       | 0           | 0          |
| [Grading](../reference-1/grading.md)               | 8       | 0           | 0          |
| [Roster](../reference-1/roster.md)                 | 2       | 2           | 0          |
| [Dashboards](../reference-1/dashboards.md)         | 2       | 0           | 2          |
| [Fees](../reference-1/fees.md)                     | 5       | 1           | 0          |
| [Parent portal](../reference-1/parents.md)         | 5       | 1           | 0          |
| [Notifications](../reference-1/notifications.md)   | 2       | 0           | 0          |
| [Student portal](../reference-1/student.md)        | 6       | 0           | 0          |
| **Total**                                          | **124** | **14**      | **2**      |

## What is blocked, and why

Ordered by how many endpoints each gap unblocks.

| Missing                       | Blocks                | Notes                                                                                                                                                                      |
| ----------------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Dashboard metrics**         | 1 endpoint, screen 6  | Not a data gap — **the four stat-card labels are blank placeholders in the wireframe source.** The endpoint cannot be specified until someone names what the numbers count |
| **Per-session TA assignment** | 1 endpoint, screen 14 | Assistants are assigned to groups, not sessions, so "today's sessions to cover" has no source                                                                              |

## Decisions worth taking early

Three of the ⚠️ items change the shape of an endpoint rather than just its behaviour. Taking them before implementation avoids rework.

**Session recurrence.** Weekly sessions write a `SESSION_SERIES` parent and materialized `LIVE_SESSIONS` rows. `PATCH` takes `scope=this|this_and_following`. Later siblings that already have attendance are **skipped** (left unchanged); the response lists `skipped_session_ids`.

**Assignment deadlines across sections.** **Decided: shared.** `ASSIGNMENTS.due_date` is one timestamp for every group. No `GROUP_ASSIGNMENTS` junction.

**Auto-finalize on grading.** **Decided: auto.** The last structured grade on an attempt flips it to `GRADED` and fires `quiz.graded`. `POST .../finalize` is an instructor override (idempotent if already graded).

**Meeting links.** **Decided: pasted URL.** Instructors paste Zoom/Meet into `meeting_url`. No OAuth credentials. The webhook stays unused until a provider is connected.

## Where this comes from

This specification is derived from three sources in the repository, not from running code:

* `docs/erd.md` — entities, constraints, delete rules
* `docs/elearning-platform-wireframes.html` — 24 screens, interactions and cross-screen sync rules
* `docs/api-resource-map.md` — the endpoint map and screen coverage matrix

When any of those change, regenerate rather than hand-editing.
