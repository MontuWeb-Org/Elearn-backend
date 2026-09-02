# Roles & access

## Roles

One login serves all four tiers. The server resolves the caller's role and returns a
`routing_target`; the client does not choose where to land.

| Code | Role | Database value |
|---|---|---|
| `I` | Instructor | `TEACHER` |
| `A` | Teaching assistant | `ASSISTANT` |
| `P` | Parent | `PARENT` |
| `S` | Student | `STUDENT` |
| `—` | Public, pre-auth | — |

`USER_ROLES` is many-to-many, so a user *may* hold several roles, but every screen assumes one role
for routing purposes.

## Role alone never authorizes

Every endpoint applies an **ownership scope** on top of the role. Holding a role grants access to
an endpoint shape; the scope decides which rows.

| Scope | Rule |
|---|---|
| `own-course` | The resource resolves to a course whose `teacher_id` is the caller |
| `assigned-group` | The caller has a non-revoked `GROUP_ASSISTANTS` row for the group **and** the relevant permission flag |
| `linked-child` | The caller has a `PARENT_STUDENTS` row for the student |
| `own-enrollment` | The caller has a `STUDENT_GROUPS` row for the group owning the resource |
| `self` | The resource is the caller's own row |

A failure of scope is `403 INSUFFICIENT_SCOPE`, not `404` — with one exception: where confirming
existence would itself leak information, the API returns `404`.

## Assistant permissions

`assigned-group` is the only scope with a second dimension. A teaching assistant's access is
controlled by two independent axes, both on `GROUP_ASSISTANTS`:

**Scope** — which groups. One row per group. "All sections" is stored as N rows, not a wildcard,
which means a TA does **not** automatically gain access to sections created later.

**Permissions** — three booleans on `GROUP_ASSISTANTS`, granted once with [Edit](../reference/assistants.md) after the TA accepts. They are not on the invite:

| Flag | Gates |
|---|---|
| `can_take_attendance` | [Attendance](../reference/attendance.md) reads and writes |
| `can_grade` | The entire [Grading](../reference/grading.md) queue |
| `can_upload_solutions` | Assignment solution upload and release |

A TA scoped to "Section A only" with "Attendance only" can read and write attendance for Section A
and nothing else. Hitting the grading queue returns `403`.

{% hint style="info" %}
**Revocation never deletes.** Grading history points at the assistant's user id, so revoking sets
`is_revoked` on their rows. Access ends immediately; every grade they gave keeps its attribution.
`USERS → GROUP_ASSISTANTS` is `RESTRICT` for the same reason.
{% endhint %}

## Account creation

Only instructors self-register. Teaching assistant, student and parent accounts are **always**
created through an [invite](../reference/invites.md). Instructors issue most of them; a student may
issue a parent invite for themselves.

## Parent access

Two invariants apply to every parent-facing endpoint, enforced in the service layer:

1. A parent reads nothing outside their linked children. Every query filters by the caller's
   `PARENT_STUDENTS` rows.
2. A parent is read-only on academic records. The single parent write in the whole API is fee
   payment.

The link is many-to-many in both directions and is deliberately not scoped to an instructor: a
parent with children under two different instructors holds one account and one set of links.
