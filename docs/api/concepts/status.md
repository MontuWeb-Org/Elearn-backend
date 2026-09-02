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
| [Authentication](../reference/authentication.md) | 4 | 5 | 2 |
| [Invites](../reference/invites.md) | 2 | 3 | 0 |
| [Billing](../reference/billing.md) | 1 | 3 | 0 |
| [Courses](../reference/courses.md) | 3 | 2 | 0 |
| [Chapters](../reference/chapters.md) | 6 | 0 | 0 |
| [Lessons](../reference/lessons.md) | 6 | 0 | 2 |
| [Materials](../reference/materials.md) | 1 | 1 | 4 |
| [Recordings](../reference/recordings.md) | 3 | 2 | 1 |
| [Uploads](../reference/uploads.md) | 0 | 1 | 0 |
| [Assignments](../reference/assignments.md) | 8 | 3 | 0 |
| [Groups](../reference/groups.md) | 4 | 4 | 0 |
| [Assistants](../reference/assistants.md) | 6 | 1 | 0 |
| [Scheduling](../reference/scheduling.md) | 2 | 3 | 2 |
| [Attendance](../reference/attendance.md) | 2 | 2 | 1 |
| [Quizzes](../reference/quizzes.md) | 8 | 2 | 0 |
| [Quiz attempts](../reference/attempts.md) | 4 | 1 | 0 |
| [Grading](../reference/grading.md) | 5 | 3 | 0 |
| [Roster](../reference/roster.md) | 2 | 2 | 0 |
| [Dashboards](../reference/dashboards.md) | 0 | 2 | 2 |
| [Fees](../reference/fees.md) | 0 | 0 | 5 |
| [Parent portal](../reference/parents.md) | 4 | 1 | 1 |
| [Notifications](../reference/notifications.md) | 1 | 1 | 0 |
| [Student portal](../reference/student.md) | 4 | 1 | 1 |
| **Total** | **76** | **44** | **21** |
## What is blocked, and why

Ordered by how many endpoints each gap unblocks.

| Missing | Blocks | Notes |
|---|---|---|
| **Fees and payments** | 6 endpoints, screens 12 and 18 | No student-payment entity exists. `COURSES.fees` is a static price tag and `SUBSCRIPTIONS` is a *different money flow* — instructor to platform. Needs `ENROLLMENT_FEES` plus `PAYMENTS`, and first needs an answer to whether fees are per course, per group, per month or per student |
| **Lesson publish state** | 3 endpoints, screens 7 and 20 | `LESSONS` has no `status`. Draft versus published gates all student and parent visibility |
| **View tracking** | 3 endpoints, screens 11 and 20 | Opening a file is meant to log a "viewed" state the instructor sees on the roster, and lesson progress chips need per-student data. Needs `MATERIAL_VIEWS` and `RECORDED_SESSION_VIEWS` — the ERD already names the latter as the natural extension |
| **Material access mode** | 3 endpoints, screen 8 | View-only versus downloadable is set at upload and has nowhere to live, along with file size and MIME type |
| **Password reset tokens** | 2 endpoints, screen 3 | No reset-token store. `INVITES` is the obvious template — hashed token, expiry, single use — but a reset is not an invite and should not share the table |
| **Meeting integration** | 2 endpoints, screens 10 and 21 | `meeting_url` is a plain string. Auto-generated links and join-log attendance need a provider, an external meeting id and a webhook ingest |
| **Partial attendance** | 1 endpoint, screen 21 | "Leaving early can flag partial attendance", but the status enum has no `PARTIAL` and there are no join or leave timestamps |
| **Dashboard metrics** | 1 endpoint, screen 6 | Not a data gap — **the four stat-card labels are blank placeholders in the wireframe source.** The endpoint cannot be specified until someone names what the numbers count |
| **Per-session TA assignment** | 1 endpoint, screen 14 | Assistants are assigned to groups, not sessions, so "today's sessions to cover" has no source |

## Decisions worth taking early

Three of the ⚠️ items change the shape of an endpoint rather than just its behaviour. Taking them
before implementation avoids rework.

**Session recurrence.** Recurring sessions are set weekly per section, and editing one occurrence
prompts "this session only" versus "this and following". Sessions are currently independent rows.
Either occurrences are materialized on create — which adds a `scope` parameter to every session
update and a server-side sibling walk — or a `SESSION_SERIES` parent is introduced. This changes
the whole session-write API.

**Assignment deadlines across sections.** An assignment's `due_date` sits on the cohort-independent
branch, so every section shares it. If Section A reaches a lesson in week 2 and Section B in week
4, one deadline cannot serve both — and on-time submission is the entire point of an assignment.
The fix is a `GROUP_ASSIGNMENTS (group_id, assignment_id, due_date)` junction. Given that the
wireframes show three concurrent sections, this will bite.

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
