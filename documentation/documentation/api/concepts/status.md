# Specification status

Every operation carries a status line. This page explains the three labels and lists what is
currently blocking what.

## The three labels

{% hint style="success" %}
**✅ Specifiable** — fully backed by the entity-relationship diagram. The request and response
shapes are final and implementation can begin.
{% endhint %}

{% hint style="warning" %}
**⚠️ Awaiting a decision** — the data exists, but a behavioural question is open. The shape shown
is the recommended reading; confirm it before building, because some of these change the endpoint,
not just its semantics.
{% endhint %}

{% hint style="danger" %}
**🚫 Blocked** — depends on an entity that does not exist in the schema. The shape shown is a
proposal to be reviewed, not a contract to build against.
{% endhint %}

## By resource group

| Group | ✅ Ready | ⚠️ Decision | 🚫 Blocked |
|---|---|---|---|
| [Authentication](../reference/authentication.md) | 11 | 0 | 0 |
| [Invites](../reference/invites.md) | 5 | 0 | 0 |
| [Billing](../reference/billing.md) | 2 | 2 | 0 |
| [Subjects](../reference/subjects.md) | 1 | 0 | 0 |
| [Courses](../reference/courses.md) | 4 | 1 | 0 |
| [Chapters](../reference/chapters.md) | 6 | 0 | 0 |
| [Lessons](../reference/lessons.md) | 8 | 0 | 0 |
| [Materials](../reference/materials.md) | 5 | 0 | 0 |
| [Recordings](../reference/recordings.md) | 5 | 0 | 0 |
| [Uploads](../reference/uploads.md) | 0 | 1 | 0 |
| [Assignments](../reference/assignments.md) | 10 | 1 | 0 |
| [Groups](../reference/groups.md) | 4 | 4 | 0 |
| [Assistants](../reference/assistants.md) | 6 | 1 | 0 |
| [Scheduling](../reference/scheduling.md) | 4 | 2 | 0 |
| [Attendance](../reference/attendance.md) | 4 | 1 | 0 |
| [Quizzes](../reference/quizzes.md) | 8 | 2 | 0 |
| [Quiz attempts](../reference/attempts.md) | 4 | 1 | 0 |
| [Grading](../reference/grading.md) | 5 | 3 | 0 |
| [Roster](../reference/roster.md) | 2 | 2 | 0 |
| [Dashboards](../reference/dashboards.md) | 1 | 1 | 2 |
| [Fees](../reference/fees.md) | 5 | 1 | 0 |
| [Parent portal](../reference/parents.md) | 5 | 1 | 0 |
| [Notifications](../reference/notifications.md) | 2 | 0 | 0 |
| [Student portal](../reference/student.md) | 5 | 1 | 0 |
| **Total** | **109** | **27** | **2** |

## What is blocked, and why

Ordered by how many endpoints each gap unblocks.

| Missing | Blocks | Notes |
|---|---|---|
| **Dashboard metrics** | 1 endpoint, screen 6 | Not a data gap — **the four stat-card labels are blank placeholders in the wireframe source.** The endpoint cannot be specified until someone names what the numbers count |
| **Per-session TA assignment** | 1 endpoint, screen 14 | Assistants are assigned to groups, not sessions, so "today's sessions to cover" has no source |

## Decisions worth taking early

Three of the ⚠️ items change the shape of an endpoint rather than just its behaviour. Taking them
before implementation avoids rework.

**Session recurrence.** Weekly sessions write a `SESSION_SERIES` parent and materialized
`LIVE_SESSIONS` rows. `PATCH` takes `scope=this|this_and_following`. Remaining open: editing
"this and following" when later occurrences already have attendance (`GAP D14`).

**Assignment deadlines across sections.** **Decided: shared.** `ASSIGNMENTS.due_date` is one timestamp for every group. No `GROUP_ASSIGNMENTS` junction.

**Auto-finalize on grading.** Either the last per-answer grade flips an attempt to `GRADED`
automatically, or finalizing stays an explicit second step. Auto fits the queue better — it serves
one answer at a time across many students and never shows a whole paper — but it decides whether
the student and parent fan-out has one trigger or two.

## Where this comes from

This specification is derived from three sources in the repository, not from running code:

* `docs/erd.md` — entities, constraints, delete rules
* `docs/elearning-platform-wireframes.html` — 24 screens, interactions and cross-screen sync rules
* `docs/api-resource-map.md` — the endpoint map and screen coverage matrix

When any of those change, regenerate rather than hand-editing.
