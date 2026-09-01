---
description: REST API for the Montu e-learning platform — instructors, assistants, parents and students on one curriculum, one schedule, one gradebook.
---

# Montu Platform API

A centralized LMS for independent IGCSE and American-Diploma instructors, replacing scattered
WhatsApp groups, Google Drives, Zoom links and external quiz tools with a single workspace.

Four linked account tiers read from the same data:

| Tier | Does | Never does |
|---|---|---|
| **Instructor** | Everything under their own courses — curriculum, content, quizzes, schedule, attendance, grading, roster, fees, team | — |
| **Teaching assistant** | Attendance, grading and solution uploads, scoped to assigned sections and behind per-action permissions | Course building, scheduling, fees, settings |
| **Parent** | Reads attendance, grades, fees and schedule for linked children; pays fees | Edits anything academic |
| **Student** | Views published lessons, joins live classes, takes quizzes, submits homework | Anything authoring |

{% hint style="warning" %}
**This is a specification, not a description of running code.**

The backend is scaffolding only. Every endpoint here is derived from the entity-relationship
diagram and the 24-screen wireframe set, and each one carries a status saying whether it is fully
backed by the schema, depends on an open decision, or is blocked on an entity that does not exist
yet. See [Specification status](concepts/status.md).
{% endhint %}

## Start here

Four concepts apply to every endpoint and are not repeated on each one.

<table data-card-size="large" data-view="cards">
<thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead>
<tbody>
<tr><td><strong>Conventions</strong></td><td>Paths, nesting, identifiers, timestamps, money, pagination.</td><td><a href="concepts/conventions.md">conventions.md</a></td></tr>
<tr><td><strong>Roles &#x26; access</strong></td><td>The four tiers, and the ownership scope every endpoint applies on top of the role.</td><td><a href="concepts/roles-and-access.md">roles-and-access.md</a></td></tr>
<tr><td><strong>The two branches</strong></td><td>Why attendance is never nested under a lesson, and assignments never under a group.</td><td><a href="concepts/two-branches.md">two-branches.md</a></td></tr>
<tr><td><strong>Errors</strong></td><td>One problem shape, and the machine codes behind each schema invariant.</td><td><a href="concepts/errors.md">errors.md</a></td></tr>
</tbody>
</table>

## Base URL and authentication

```
https://api.montu.example/api/v1
```

Every request except six public endpoints carries a bearer token:

```http
Authorization: Bearer <access_token>
```

Get one from [`POST /auth/login`](reference/authentication.md). Access tokens are short-lived;
refresh tokens rotate on every use.

## Quick orientation

* **Building a syllabus?** [Courses](reference/courses.md) → [Chapters](reference/chapters.md) → [Lessons](reference/lessons.md) → [Materials](reference/materials.md)
* **Running classes?** [Groups](reference/groups.md) → [Scheduling](reference/scheduling.md) → [Attendance](reference/attendance.md)
* **Assessing?** [Assignments](reference/assignments.md) for homework, [Quizzes](reference/quizzes.md) → [Quiz attempts](reference/attempts.md) → [Grading](reference/grading.md) for tests
* **Reading progress?** [Roster](reference/roster.md), [Dashboards](reference/dashboards.md), [Parent portal](reference/parents.md)
