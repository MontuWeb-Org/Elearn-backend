# API Resource Map

The index for the API documentation effort. Every screen in `docs/elearning-platform-wireframes.html` is mapped to the resources it reads and writes; every resource is mapped back to the ERD entities behind it and to the gaps that block it.

**Sources**
| Ref | File | Authoritative for |
|---|---|---|
| `SCOPE` | `Montu - E-Learning Platform.md` | Vision, four tiers, feature pillars |
| `ERD` | `erd.md` | Entities, constraints, delete rules |
| `WF` | `elearning-platform-wireframes.html` | 24 screens (`s-*`), interactions, sync promises |
| `GAP` | `erd-wireframe-gap-analysis.md` | Findings A/B/C/D/E |
| `NOTES` | `api-source-analysis.md` | Gaps G1–G16, conventions |
| `DEMO` | `API Docs.md` | Per-page documentation template (screen 07) |

**How to read this document**

1. §1–§3 fix the conventions every endpoint doc inherits, so no per-page doc restates them.
2. §4 is the resource inventory — one row per resource root.
3. §5 is the endpoint map, grouped by domain. This is the working surface.
4. §6 is the screen → endpoint matrix: the checklist for writing the 23 per-page docs.
5. §7 lists what cannot be specified yet and why.
6. §8 is the error catalog; §9 is the writing order.

**Status legend**

| Tag | Meaning |
|---|---|
| ✅ | Fully backed by the ERD — spec can be written today |
| ⚠️ | Backed, but depends on a decision in `GAP §D` / `NOTES §9` |
| 🚫 | Blocked on a missing entity (`NOTES §7`, gaps G1–G16) — shape is proposed, not specifiable |

---

## 1. Path & naming conventions

**Base path:** `/api/v1`. The `DEMO` file writes `/api/chapters/{course-id}`; it is unversioned and pre-decision. Every path below adds the version segment and this map is the reference, not the demo.

**Nesting rule — one level of parent only.** A collection is nested under the parent that owns it; an individual item is addressed flat by its own id.

```
GET   /api/v1/courses/{courseId}/chapters      collection, scoped by owner
POST  /api/v1/courses/{courseId}/chapters      create inside owner
GET   /api/v1/chapters/{chapterId}             item, flat
PATCH /api/v1/chapters/{chapterId}             item, flat
```

This matches how `DEMO` already writes `PATCH /api/chapters/{chapter-id}` and `DELETE /api/lessons/{lesson-id}`, and it keeps paths from growing to `/courses/{}/chapters/{}/lessons/{}/materials/{}`.

**Two corrections to `DEMO` that this map applies:**

| `DEMO` writes | Should be | Why |
|---|---|---|
| `POST /api/lessons/{course-id}` | `POST /api/v1/chapters/{chapterId}/lessons` | `LESSONS.chapter_id` is the FK (`ERD:112-118`). A lesson has no direct course parent; the course is derived through the chapter |
| `GET /api/chapters/{course-id}` returning nested `lessons[]` | keep, as `GET /api/v1/courses/{courseId}/chapters?include=lessons` | The builder (WF 07) needs the whole tree in one call, but the default collection response should not silently nest. Make the expansion explicit |

**Casing:** paths `kebab-case`, JSON fields `snake_case` to mirror the ERD column names (`course_id`, `order_index`, `scheduled_start`). `DEMO` mixes `course_id` and `lesson-id` — `snake_case` wins in bodies, `kebab-case` in paths.

**Identifiers:** all resource ids are UUID v4 strings. `DEMO`'s `"course_id":"fn1o380d"` is placeholder text, not a format decision.

**Timestamps:** ISO-8601 with `Z`, always UTC. Rendering per viewer timezone is a client concern (`GAP D24`).

**Money and scores:** decimal-as-string (`"250.00"`) to avoid float loss. A single implied currency until `GAP C19` is resolved.

---

## 2. Cross-cutting contracts

**Auth.** `Authorization: Bearer <access_token>` on everything except the six public endpoints marked `—` in the role column. Access token short-lived; refresh token rotates against `USER_SESSIONS.refresh_token_hash` (`ERD:39-49`). "Remember me" (WF 01) extends refresh lifetime only.

**Role codes used in every table below**

| Code | Role | ERD value |
|---|---|---|
| `I` | Instructor | `TEACHER` |
| `A` | Teaching assistant | `ASSISTANT` |
| `P` | Parent | 🚫 no role value exists (`G1`) |
| `S` | Student | `STUDENT` |
| `—` | Public / pre-auth | — |

Role alone never authorizes. Every endpoint additionally applies one **ownership scope**:

| Scope | Rule |
|---|---|
| `own-course` | The resource resolves to a course whose `teacher_id` is the caller |
| `assigned-group` | The caller has a `GROUP_ASSISTANTS` row for the group, **and** the matching permission flag (`G6`) |
| `linked-child` | The caller is linked to the student (`G1`) |
| `own-enrollment` | The caller has a `STUDENT_GROUPS` row for the group that owns the resource |
| `self` | The resource is the caller's own user row |

**List envelope.** Every collection response:

```json
{
  "data": [],
  "page": { "limit": 25, "cursor": null, "next_cursor": "…", "total": 158 }
}
```

**Errors.** One problem shape everywhere, with a machine code from §8:

```json
{
  "error": {
    "code": "LESSON_COURSE_MISMATCH",
    "message": "The lesson does not belong to this group's course.",
    "details": [{ "field": "lesson_id", "issue": "cross_course_reference" }]
  }
}
```

`DEMO`'s `{"error": "Invalid request"}` is replaced by this shape.

**Bulk is first class.** "Mark all present" (WF 10), drag-reorder at every level (WF 07), and bulk grade save (WF 15) are single requests, not loops. Ahmed manages 150+ students (`SCOPE §4 P1`).

**Derived fields are computed on read and never stored** (`GAP E11`): attendance %, average grade, pending-grading counts, lesson progress, revenue aggregates.

---

## 3. The structural rule every path obeys

`ERD:1-11` splits the old `SESSIONS` table into two branches. **Paths must never cross them.**

```
CURRICULUM — authored once, cohort-independent
  /courses/{}/chapters/{}/lessons/{} → /materials, /recordings

COHORTS — per class instance
  /courses/{}/groups/{} → /live-sessions/{} → /attendance
                        → /assessments/{}  → /questions, /submissions
```

Consequences:

- **Attendance is never nested under a lesson.** It hangs off a `LIVE_SESSIONS` row only (`ERD:176-183`).
- **Materials and recordings are never nested under a group.** They belong to the lesson and are identical for every group of the course (`GAP E4`).
- A student reaches curriculum *through* a group enrollment, which is why the student-facing reads live under `/me/...` and not under `/courses/...`.

---

## 4. Resource inventory

| # | Resource root | Backing entities | Primary screens |
|---|---|---|---|
| R1 | `/auth` | `USERS`, `USER_SESSIONS`, `USER_ROLES` | 01, 02, 03 |
| R2 | `/invites` | 🚫 `INVITES` (`G4`) | 04, 05, 13 |
| R3 | `/me` | `USERS`, `TEACHERS`, `STUDENTS` | 13, 19 |
| R4 | `/plans`, `/subscriptions` | `SUBSCRIPTION_PLANS`, `SUBSCRIPTIONS` | 02, 13 |
| R5 | `/courses` | `COURSES` | 06, 07 |
| R6 | `/chapters` | `CHAPTERS` | 07 |
| R7 | `/lessons` | `LESSONS` | 07, 08, 20 |
| R8 | `/materials` | `MATERIALS` | 08, 20 |
| R9 | `/recordings` | `RECORDED_SESSIONS` | 08, 20 |
| R10 | `/uploads` | — (transport only, `GAP E18`) | 08, 15, 23 |
| R11 | `/groups` | `GROUPS`, `STUDENT_GROUPS`, `GROUP_ASSISTANTS` | 09, 11, 13 |
| R12 | `/assistants` | `GROUP_ASSISTANTS` + 🚫 permissions (`G6`) | 04, 13 |
| R13 | `/live-sessions` | `LIVE_SESSIONS` | 09, 10, 14, 16, 21 |
| R14 | `/attendance` | `ATTENDANCE` | 10, 16, 21 |
| R15 | `/assessments` | `ASSESSMENTS`, `ASSESSMENT_QUESTIONS` | 08, 15, 22, 23 |
| R16 | `/attempts` | 🚫 attempt state (`A12`, `G9`) | 22 |
| R17 | `/submissions` | `ASSESSMENT_SUBMISSIONS`, `..._ANSWERS` | 15, 22, 23 |
| R18 | `/students` | `STUDENTS` + derived aggregates | 11 |
| R19 | `/dashboards` | derived across all | 06, 14, 17, 19 |
| R20 | `/fees`, `/payments` | 🚫 `PAYMENTS` (`G2`) | 12, 18 |
| R21 | `/children` | 🚫 `PARENT_STUDENTS` (`G1`) | 17, 18 |
| R22 | `/notifications` | `NOTIFICATIONS` | 12, 17 |
| R23 | `/events` | — (SSE transport, `GAP D23`) | 08, 09, 10, 15, 16, 17, 18 |

---

## 5. Endpoint map

### 5.1 Authentication & identity — R1, R3

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| POST | `/auth/login` | Email + password → access + refresh. Resolves role server-side and returns the routing target | `—` | — | 01 | ✅ |
| POST | `/auth/refresh` | Rotate refresh token against `USER_SESSIONS` | `—` | — | — | ✅ |
| POST | `/auth/logout` | Revoke current `USER_SESSIONS` row (`is_revoked`) | all | `self` | — | ✅ |
| POST | `/auth/register` | Instructor self-signup, step 1 of 3. Creates `USERS` + `TEACHERS` + `USER_ROLES(TEACHER)` | `—` | — | 02 | ⚠️ |
| GET | `/auth/me` | Current user, roles, routing target | all | `self` | all | ✅ |
| POST | `/auth/password/forgot` | Request reset link. **Uniform 202 whether or not the email exists** (`WF 03`) | `—` | — | 03 | 🚫 `G5` |
| POST | `/auth/password/reset` | Consume token, set new password | `—` | — | 03 | 🚫 `G5` |
| GET | `/me/profile` | Profile tab | all | `self` | 13, 19 | ⚠️ |
| PATCH | `/me/profile` | Edit profile | all | `self` | 13, 19 | ⚠️ |
| GET | `/me/sessions` | Active devices — `USER_SESSIONS` has `user_agent`/`ip_address` with no screen (`GAP B3`) | all | `self` | — | ⚠️ |
| DELETE | `/me/sessions/{sessionId}` | Revoke one device | all | `self` | — | ⚠️ |

**Notes.** `POST /auth/register` is ⚠️ because WF 02 captures *full name* as one field, *subject(s)* plural, and a curriculum enum, none of which the ERD holds (`GAP A21`, `G16`). Document the request body against the wireframe and flag the three fields as pending schema changes.

### 5.2 Invites & onboarding — R2 🚫 `G4`

No `INVITES` entity exists. Every non-instructor account arrives this way (`NOTES §4`), so this is the highest-priority gap.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| POST | `/invites` | Issue invite. Body carries `role`, `email`, and a role-shaped `scope` (groups + permissions for TA; `student_id` for parent) | `I` | `own-course` | 13, 05 | 🚫 |
| GET | `/invites` | Pending invites list | `I` | `own-course` | 13 | 🚫 |
| DELETE | `/invites/{inviteId}` | Rescind a pending invite | `I` | `own-course` | 13 | 🚫 |
| GET | `/invites/{token}` | **Public** preview — inviter name, role, and the scope sentence rendered on WF 04 ("attendance, grading, and homework uploads") | `—` | — | 04, 05 | 🚫 |
| POST | `/invites/{token}/accept` | Create the account, apply scope, return tokens + routing target | `—` | — | 04, 05 | 🚫 |

**Notes.** `GET /invites/{token}` must return the scope in human-readable form — WF 04 shows the TA their boundaries before they activate. Parent acceptance auto-approves the child link with no manual matching (`WF 05`), which is a decision to record, not a workflow to build (`GAP D12`).

### 5.3 Billing — R4

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/plans` | Plan tiers for signup step 2 | `—` | — | 02 | ⚠️ |
| POST | `/subscriptions` | Signup step 3 — payment, creates `SUBSCRIPTIONS` | `I` | `self` | 02 | ⚠️ |
| GET | `/me/subscription` | Billing tab | `I` | `self` | 13 | ✅ |
| PATCH | `/me/subscription` | Change plan / cancel | `I` | `self` | 13 | ⚠️ |

**Notes.** ⚠️ on `/plans`: WF 02 sizes the plan on "student count **and TA seats**" but `SUBSCRIPTION_PLANS` has only `max_students` (`GAP D20`). Payment processing itself is out of scope for the resource API — assume a provider token in the body.

### 5.4 Curriculum: courses — R5

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/courses` | Instructor's courses. Filters: `status`, `grade_level` | `I` `A` | `own-course` / `assigned-group` | 06, 07 | ✅ |
| POST | `/courses` | Create course | `I` | `self` | 02, 07 | ✅ |
| GET | `/courses/{courseId}` | Course header — WF 07's "IG Physics — Term 1" | `I` `A` | `own-course` | 07 | ✅ |
| PATCH | `/courses/{courseId}` | Rename, edit description, change `status` | `I` | `own-course` | 07 | ✅ |
| DELETE | `/courses/{courseId}` | Cascades the curriculum spine (`ERD:322-335`) | `I` | `own-course` | — | ⚠️ |
| GET | `/courses/{courseId}/tree` | **The builder read.** Chapters + lessons + counts + publish state in one call | `I` `A` | `own-course` | 07 | ⚠️ |

**Notes.** `DELETE` is ⚠️ — no screen offers it and `GAP D26` flags deletion-vs-archival as undecided. Document it as existing but note that the UI exposes no path to it. `/tree` is ⚠️ pending the lesson `status` field (`G3`).

### 5.5 Curriculum: chapters — R6

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/courses/{courseId}/chapters` | Chapters, `order_index` ascending. `?include=lessons` nests them (this is `DEMO`'s "Get Chapters Related to a Course") | `I` `A` | `own-course` | 07 | ✅ |
| POST | `/courses/{courseId}/chapters` | "+ Add Chapter". `order_index` appends if omitted | `I` | `own-course` | 07 | ✅ |
| GET | `/chapters/{chapterId}` | Single chapter | `I` `A` | `own-course` | 07 | ✅ |
| PATCH | `/chapters/{chapterId}` | "Edit" — title, description | `I` | `own-course` | 07 | ✅ |
| DELETE | `/chapters/{chapterId}` | Cascades to lessons, materials, recordings | `I` | `own-course` | 07 | ✅ |
| PUT | `/courses/{courseId}/chapters/order` | **Bulk reorder** — body is the full ordered `chapter_id` array. One request per drag-drop | `I` | `own-course` | 07 | ✅ |

**Notes.** `UNIQUE (course_id, order_index)` (`ERD:277-287`) means naive per-item reorder produces transient collisions. The bulk `PUT` reassigns the whole sequence in one transaction — this is why reorder is not a `PATCH` on the item.

### 5.6 Curriculum: lessons — R7

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/chapters/{chapterId}/lessons` | Lessons in order | `I` `A` | `own-course` | 07 | ✅ |
| POST | `/chapters/{chapterId}/lessons` | "+ Add Lesson" — corrects `DEMO`'s `POST /api/lessons/{course-id}` | `I` | `own-course` | 07 | ✅ |
| GET | `/lessons/{lessonId}` | Lesson header for the Content Hub | `I` `A` | `own-course` | 08 | ✅ |
| PATCH | `/lessons/{lessonId}` | Title, description | `I` | `own-course` | 07, 08 | ✅ |
| DELETE | `/lessons/{lessonId}` | Cascades materials + recordings; **`SET NULL` on `LIVE_SESSIONS.lesson_id`** | `I` | `own-course` | 07 | ✅ |
| PUT | `/chapters/{chapterId}/lessons/order` | Bulk reorder within a chapter | `I` | `own-course` | 07 | ✅ |
| POST | `/lessons/{lessonId}/publish` | Draft → Published; makes it visible on WF 20 | `I` | `own-course` | 07 | 🚫 `G3` |
| POST | `/lessons/{lessonId}/unpublish` | Published → Draft | `I` | `own-course` | 07 | 🚫 `G3` |

**Notes.** The `DELETE` doc must state the `SET NULL` behaviour explicitly: **deleting a lesson never destroys attendance history** (`ERD:322-335`). A live session that covered the lesson survives with `lesson_id = null`. Publish/unpublish is modelled as a state transition endpoint rather than a `PATCH` field so the real-time fan-out to WF 20 and WF 17 has one hook.

### 5.7 Materials & recordings — R8, R9, R10

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/lessons/{lessonId}/materials` | Files list — name, size, type, access mode | `I` `A` `S` | `own-course` / `own-enrollment` | 08, 20 | ⚠️ |
| POST | `/lessons/{lessonId}/materials` | Attach an uploaded file. Body sets `access_mode` (view-only / downloadable) | `I` `A` | `own-course` / `assigned-group`+upload | 08 | 🚫 `G7` |
| PATCH | `/materials/{materialId}` | Rename, change access mode | `I` | `own-course` | 08 | 🚫 `G7` |
| DELETE | `/materials/{materialId}` | Remove file | `I` | `own-course` | 08 | ✅ |
| GET | `/materials/{materialId}/content` | Issue a short-lived signed URL, honouring `access_mode` | `S` `P` `I` `A` | `own-enrollment` | 20 | 🚫 `G7` |
| POST | `/materials/{materialId}/views` | Log the "viewed" state WF 20 promises the roster will show | `S` | `own-enrollment` | 20 | 🚫 `G8` |
| GET | `/lessons/{lessonId}/recordings` | Recordings for a lesson | `I` `A` `S` | as above | 08, 20 | ✅ |
| POST | `/lessons/{lessonId}/recordings` | Add recording — `video_url`, `duration_seconds`, `publish_at`, `deadline`, `max_watch_limit` | `I` | `own-course` | 08 | ⚠️ |
| PATCH | `/recordings/{recordingId}` | Edit gating fields | `I` | `own-course` | 08 | ⚠️ |
| DELETE | `/recordings/{recordingId}` | Remove | `I` | `own-course` | 08 | ✅ |
| PUT | `/lessons/{lessonId}/recordings/order` | Bulk reorder | `I` | `own-course` | 08 | ✅ |
| POST | `/recordings/{recordingId}/views` | View log — the basis for `max_watch_limit` enforcement | `S` | `own-enrollment` | 20 | 🚫 `G8` |
| POST | `/uploads` | Request an upload target (signed PUT). Returns `file_url` to pass to the material/recording/submission create | `I` `A` `S` | `self` | 08, 15, 23 | ⚠️ |

**Notes.** `GET /lessons/{lessonId}/materials` is ⚠️ because WF 08 shows "1.2 MB" and a type icon, and neither `size` nor `mime_type` exists on `MATERIALS` (`GAP A9`, `C11`). Recording writes are ⚠️ because `publish_at` / `deadline` / `max_watch_limit` are declarative and unenforced in this pass (`ERD:337-345`, `GAP E14`) — the fields accept values, the platform does not police them yet. Say so in the endpoint doc rather than implying enforcement.

### 5.8 Cohorts: groups, enrollment, assistants — R11, R12

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/courses/{courseId}/groups` | The "sections" — Section A / B / Revision | `I` `A` | `own-course` | 09, 11, 13 | ✅ |
| POST | `/courses/{courseId}/groups` | Create a section | `I` | `own-course` | 09 | ✅ |
| GET | `/groups/{groupId}` | Section header, defaults, capacity | `I` `A` | `assigned-group` | 11 | ✅ |
| PATCH | `/groups/{groupId}` | Name, `schedule_info`, `classroom_location`, `max_capacity` | `I` | `own-course` | 09 | ⚠️ |
| POST | `/groups/{groupId}/archive` | **Archive, not delete** — `GROUPS → LIVE_SESSIONS` is `RESTRICT` | `I` | `own-course` | — | ⚠️ |
| GET | `/groups/{groupId}/students` | Section roster | `I` `A` | `assigned-group` | 10, 11, 16 | ✅ |
| POST | `/groups/{groupId}/students` | Enroll (bulk: accepts an array) | `I` | `own-course` | 11 | ✅ |
| DELETE | `/groups/{groupId}/students/{studentId}` | Unenroll | `I` | `own-course` | 11 | ⚠️ |
| GET | `/assistants` | TA list with scope + permissions — the WF 13 table | `I` | `own-course` | 13 | 🚫 `G6` |
| GET | `/assistants/{userId}` | One TA's scope | `I` | `own-course` | 13 | 🚫 `G6` |
| PATCH | `/assistants/{userId}` | "Edit" — change section scope and per-action permissions | `I` | `own-course` | 13 | 🚫 `G6` |
| POST | `/assistants/{userId}/revoke` | Remove access **without deleting grading history** | `I` | `own-course` | 13 | 🚫 `G6` |

**Notes.** WF 13 shows Scope ("All sections" / "Section A only") and Permissions ("Grading, Attendance" / "Attendance only") as two independent axes. `GROUP_ASSISTANTS` is a bare composite-PK join (`ERD:152-156`), so both axes are unrepresentable today. "All sections" also has to answer whether it auto-includes future groups (`GAP D10`) — a stored wildcard, not an enumeration, if the answer is yes. Revocation must preserve `ASSESSMENT_SUBMISSIONS.graded_by_user_id` history, so it is a state flag, never a row delete (`GAP D31`).

`PATCH /groups/{groupId}` is ⚠️: WF 09 never edits `schedule_info` or `classroom_location` and no screen shows `max_capacity` (`GAP B12`, `B13`). The fields exist; nothing drives them.

### 5.9 Scheduling — R13

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/live-sessions` | **The timetable query.** Filters: `from`, `to`, `group_id`, `course_id`, `mode`, `status`. Mirrors index `LIVE_SESSIONS (group_id, scheduled_start)` | `I` `A` `S` `P` | role-shaped | 09, 06, 14, 19, 18 | ✅ |
| POST | `/live-sessions` | "+ New Session" — online (`meeting_url`) or offline (`classroom_location`) | `I` | `own-course` | 09 | ⚠️ |
| GET | `/live-sessions/{sessionId}` | Session detail for the Class Session View | `I` `A` | `assigned-group` | 10, 16, 21 | ✅ |
| PATCH | `/live-sessions/{sessionId}` | Edit time, room, mode, linked lesson | `I` | `own-course` | 09 | ⚠️ |
| POST | `/live-sessions/{sessionId}/cancel` | Set `status = CANCELLED` | `I` | `own-course` | — | ⚠️ |
| GET | `/live-sessions/{sessionId}/join` | Returns the embed target plus whether the join window is open; drives WF 19's "Join Now vs countdown" | `S` | `own-enrollment` | 19, 21 | 🚫 `A15` |
| POST | `/webhooks/meetings/{provider}` | Ingest a provider join log for auto-attendance | `—` | signature | 10, 21 | 🚫 `G15` |

**Notes — the recurrence problem.** WF 09 promises weekly recurring sessions per section, and editing one occurrence prompts *"this session only"* vs *"this and following"*. `LIVE_SESSIONS` rows are independent and `GROUPS.schedule_info` is explicitly a free-text hint, not truth (`ERD:337-345`). This is `G10`, and it changes the entire session-write API:

- **Materialize-on-create** — `POST /live-sessions` with a `recurrence` block writes N rows. `PATCH` then needs a `scope=this|this_and_following` query parameter and a server-side sibling walk.
- **`SESSION_SERIES` parent** — sessions carry a `series_id`; edits target the series or detach one occurrence.

Neither is decidable from the current ERD. Both `POST` and `PATCH` stay ⚠️ until one is chosen, and `GAP D14` (editing "this and following" when later occurrences already have attendance) must be answered with it.

`POST /live-sessions` also carries two CHECK constraints as `422`s: `mode=ONLINE ⇒ meeting_url` required, `mode=ONSITE ⇒ classroom_location` required, plus `scheduled_end > scheduled_start` (`ERD:288-294`). And the cross-branch invariant: if `lesson_id` is set, the lesson's course must equal the group's course (`ERD:295-304`).

`/cancel` is ⚠️ — the enum value exists but no screen offers the action, and whether a cancelled session leaves the attendance denominator is undecided (`GAP D15`, `E15`).

### 5.10 Attendance — R14

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/live-sessions/{sessionId}/attendance` | The checkable roster — one row per enrolled student, with any recorded status | `I` `A` | `assigned-group`+attendance | 10, 16 | ⚠️ |
| PUT | `/live-sessions/{sessionId}/attendance` | **Bulk save.** Body is the full status array — this is both "Mark all present" and "Save Attendance" | `I` `A` | `assigned-group`+attendance | 10, 16 | ✅ |
| PATCH | `/attendance/{attendanceId}` | Single-student override | `I` `A` | `assigned-group`+attendance | 10 | ✅ |
| POST | `/live-sessions/{sessionId}/end` | "End Session & Save Attendance" — commits attendance, sets `status = COMPLETED`, **fires the parent-badge fan-out** | `I` `A` | `assigned-group`+attendance | 10 | ✅ |
| POST | `/live-sessions/{sessionId}/attendance/self` | Auto-mark on join from the Live Class screen | `S` | `own-enrollment` | 21 | ⚠️ |

**Notes.** `GET .../attendance` is ⚠️ for a subtle reason worth writing into the doc: group membership is current-state only (`GAP E7`, `C14`). Re-opening a past session reconstructs its roster from *today's* membership, so a student who left the section disappears from a session they attended. The response should therefore be built from recorded `ATTENDANCE` rows **unioned with** current membership, not from membership alone.

`POST .../attendance/self` is ⚠️: WF 21 says leaving early "can flag partial attendance", but `ATTENDANCE.status` is `PRESENT/ABSENT/LATE` with no `PARTIAL` and no join/leave timestamps (`G13`). It also collides with manual marking — which value wins, and who recorded it, is undecided and `ATTENDANCE` has no `recorded_by` column (`GAP D5`).

### 5.11 Assessments — R15

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/assessments` | Filters: `group_id`, `lesson_id`, `type`, `due_before`. Mirrors index `ASSESSMENTS (group_id, due_date)` | `I` `A` `S` | role-shaped | 06, 14, 19 | ✅ |
| POST | `/assessments` | Create a quiz or assignment. Authored in lesson context, but `group_id` is mandatory | `I` `A` | `own-course` | 08 | ⚠️ |
| GET | `/assessments/{assessmentId}` | Detail, with questions for the builder | `I` `A` | `own-course` | 08, 15 | ✅ |
| PATCH | `/assessments/{assessmentId}` | Title, `due_date`, `max_score` | `I` | `own-course` | 08 | ✅ |
| DELETE | `/assessments/{assessmentId}` | Remove | `I` | `own-course` | 08 | ✅ |
| POST | `/assessments/{assessmentId}/publish` | Make visible to students; fires the WF 20 / WF 17 fan-out | `I` | `own-course` | 08 | ⚠️ |
| GET | `/assessments/{assessmentId}/questions` | Question list | `I` `A` | `own-course` | 08 | ✅ |
| POST | `/assessments/{assessmentId}/questions` | "+ Add Question" — `MCQ` carries `options` + `model_answer` | `I` | `own-course` | 08 | ⚠️ |
| PATCH | `/questions/{questionId}` | Edit | `I` | `own-course` | 08 | ✅ |
| DELETE | `/questions/{questionId}` | Remove | `I` | `own-course` | 08 | ✅ |
| POST | `/assessments/{assessmentId}/solutions` | TA uploads homework solution files | `I` `A` | `assigned-group`+upload | 15 | 🚫 `A19` |

**Notes.** `POST /assessments` is the sharpest ambiguity in the whole map (`GAP D1`). A quiz is authored **inside a lesson** on WF 08, but `ASSESSMENTS.group_id` is mandatory and no screen asks which section the quiz is for. Two readings:

- **Fan-out** — one authoring action writes N assessment rows, one per targeted group. Grading queues stay per-section; edits must fan out too.
- **Shared** — one row, with `group_id` relaxed to a join table.

`GAP E9` assumes fan-out with explicitly chosen groups. Until confirmed, `POST /assessments` takes `group_ids[]` and the doc states the fan-out plainly.

`POST .../questions` is ⚠️: the builder distinguishes only MCQ vs "structured answer", while the enum has `MCQ, ESSAY, TEXT, FILE_UPLOAD` (`GAP B16`). Either the UI selects among three, or three collapse to one.

`ASSESSMENTS` also has no `duration_seconds`, so the WF 22 countdown has nothing behind it (`G9`) — see §5.12.

### 5.12 Quiz attempts — R16 🚫 `A12`, `G9`

`ASSESSMENT_SUBMISSIONS` models a *completed* submission only — `submitted_at` and no attempt state (`ERD:205-215`). WF 22 requires a live attempt: a countdown, a question navigator, and per-answer state before final submit. This is a missing entity, not a missing field.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| POST | `/assessments/{assessmentId}/attempts` | Start. Returns `started_at`, `expires_at`, questions | `S` | `own-enrollment` | 22 | 🚫 |
| GET | `/attempts/{attemptId}` | Resume — answers so far, time remaining, per-question answered flags for the navigator | `S` | `self` | 22 | 🚫 |
| PATCH | `/attempts/{attemptId}/answers` | Autosave one or more answers | `S` | `self` | 22 | 🚫 |
| POST | `/attempts/{attemptId}/submit` | Finalize → creates the `ASSESSMENT_SUBMISSIONS` row, auto-grades MCQs immediately | `S` | `self` | 22 | 🚫 |

**Notes.** Three decisions ride on this: what timer expiry does (auto-submit / lock / grace, `GAP D17`); how a provisional MCQ-only score is represented distinctly from the final `total_score` (`GAP C10`); and what status a mixed submission holds between auto-grading and human grading (`GAP D18`) — which is also what the "24 pending" badge on WF 06 and WF 14 counts.

### 5.13 Submissions & grading — R17

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| POST | `/assessments/{assessmentId}/submissions` | Homework submit — `file_url` + optional student note | `S` | `own-enrollment` | 23 | ⚠️ |
| GET | `/assessments/{assessmentId}/submissions` | Grading queue for one assessment. Filter `status=pending_manual` | `I` `A` | `assigned-group`+grading | 15 | ⚠️ |
| GET | `/submissions/{submissionId}` | One submission with all answers | `I` `A` `S` | scoped | 15, 22, 23 | ✅ |
| PATCH | `/submissions/{submissionId}` | Re-submit before grading | `S` | `self` | 23 | 🚫 `G12` |
| PATCH | `/submissions/{submissionId}/answers/{answerId}` | Score + comment one structured answer — "/ 2 pts · Save" | `I` `A` | `assigned-group`+grading | 15 | ✅ |
| POST | `/submissions/{submissionId}/grade` | Finalize: total, feedback, `status = GRADED`, **locks re-submission**, fires student + parent fan-out | `I` `A` | `assigned-group`+grading | 15 | ⚠️ |
| GET | `/grading/queue` | **Cross-assessment queue.** Structured answers awaiting a human, across every assigned group | `I` `A` | `assigned-group`+grading | 06, 14, 15 | ⚠️ |

**Notes.** `POST .../submissions` is ⚠️ on two counts: the student's "Notes for your teacher" has no column (`GAP A20` — `feedback_comments` is grader-side), and lateness. WF 23 requires the `Late` flag to persist *next to a grade* and stay visible to instructor and parent, but `LATE` and `GRADED` are values of the *same* enum (`G11`, `GAP D8`) — a late-then-graded submission loses its lateness. Split into `status` + `is_late`.

`PATCH /submissions/{id}` is blocked because re-submission semantics are undefined (`G12`, `GAP D7`): new row per attempt or overwrite, and whether lateness is re-evaluated each time. The lock is documented as `409 SUBMISSION_LOCKED` once `status = GRADED`.

`GET /grading/queue` is ⚠️ because "pending" needs a definition (`GAP D18`) and WF 15's "MCQs auto-graded — 18/24 already complete" needs per-question grading progress that a single nullable `total_score` cannot express (`GAP C9`).

`POST .../grade` is ⚠️ on `GAP D9`: whether an instructor can regrade after a TA, and whether `graded_by_user_id` — a single field — records the last grader or the first (`GAP E12` assumes last).

### 5.14 Roster & aggregates — R18, R19

Everything here is computed on read (`GAP E11`).

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/students` | The 158-row roster. Filters: `group_id`, `attendance_below`, `homework_status`, `q`. Returns attendance %, last quiz %, homework state | `I` `A` | `own-course` | 11 | ⚠️ |
| GET | `/students/{studentId}` | Detail panel: full attendance history, quiz/homework record, linked parent contact | `I` `A` | `own-course` | 11 | 🚫 `G1` |
| GET | `/students/{studentId}/attendance` | Per-session history | `I` `A` `P` | scoped | 11, 18 | ✅ |
| GET | `/students/{studentId}/grades` | Graded submissions | `I` `A` `P` | scoped | 11, 18 | ✅ |
| GET | `/dashboards/instructor` | WF 06 — four stat cards, today's sessions, pending-grading count | `I` | `own-course` | 06 | 🚫 `C3` |
| GET | `/dashboards/assistant` | WF 14 — assigned sections, pending count, today's sessions to cover | `A` | `assigned-group` | 14 | 🚫 `C15` |
| GET | `/dashboards/student` | WF 19 — next session + join window, due-soon across courses, recent grades | `S` | `self` | 19 | ⚠️ |
| GET | `/dashboards/parent` | WF 17 — child cards + activity feed | `P` | `linked-child` | 17 | 🚫 `G1` |

**Notes.** `GET /students` is ⚠️ on three counts: the `Section` column assumes one group per student, but `STUDENT_GROUPS` is many-to-many (`GAP C13`, `D4`); "Missing" homework is the *absence* of a row, requiring a defined expected-assessment set and a deadline-passed rule the ERD does not encode (`GAP C4`); and the attendance-% denominator is undefined until cancelled-session handling is settled (`GAP C16`, `D15`).

`GET /dashboards/instructor` is 🚫 for a documentation reason, not a data one: **the four stat-card labels are blank placeholder bars in the wireframe source.** Only three deep-link targets are named (roster, courses, schedule); the fourth metric is undefined (`GAP C3`). The endpoint cannot be specified until someone says what the numbers count.

`GET /dashboards/assistant` is 🚫 because `GROUP_ASSISTANTS` assigns a TA to a *group*, not a session — "today's sessions to cover" implies a per-session assignment that does not exist (`GAP C15`).

### 5.15 Fees & payments — R20 🚫 `G2`

No student-payment entity exists anywhere. `COURSES.fees` is one static decimal and `SUBSCRIPTIONS` is a *different money flow* — instructor → platform, not student → instructor. Every endpoint here is a proposal.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/fees/summary` | "This month", "Outstanding", "Paid on time 91%" | `I` | `own-course` | 12 | 🚫 |
| GET | `/fees` | Per-student fee rows: student, section, plan, status | `I` | `own-course` | 12 | 🚫 |
| POST | `/fees/{feeId}/remind` | "Send reminder" → notifies the linked parent | `I` | `own-course` | 12 | 🚫 |
| GET | `/fees/{feeId}/receipt` | Receipt document | `I` `P` | scoped | 12, 18 | 🚫 |
| GET | `/children/{studentId}/fees` | Parent-side fee tab | `P` | `linked-child` | 18 | 🚫 |
| POST | `/payments` | Parent pays; clears the overdue badge in real time | `P` | `linked-child` | 18 | 🚫 |

**Notes.** Before any of this can be specified, `GAP D19` must be answered: WF 12 shows a per-student "Plan: Monthly" column while `COURSES.fees` is a single decimal — so are fees per course, per group, per month, or per student? The proposed shape is `ENROLLMENT_FEES` (student × group × period, status `PAID/DUE/OVERDUE`) plus `PAYMENTS`, kept strictly separate from `SUBSCRIPTIONS`.

### 5.16 Parent portal — R21 🚫 `G1`

The parent tier has **no role value and no link entity**. `ROLES` is `TEACHER, STUDENT, ASSISTANT, ADMIN`; the only parent trace in the ERD is `STUDENTS.parent_phone`, a plain string. Four screens and a whole persona depend on this.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/me/children` | The child switcher — one card per linked child with attendance %, average, fee badge | `P` | `linked-child` | 17 | 🚫 |
| GET | `/children/{studentId}` | Child header + summary | `P` | `linked-child` | 18 | 🚫 |
| GET | `/children/{studentId}/attendance` | Attendance tab, read-only | `P` | `linked-child` | 18 | 🚫 |
| GET | `/children/{studentId}/grades` | Grades tab, read-only | `P` | `linked-child` | 18 | 🚫 |
| GET | `/children/{studentId}/schedule` | Schedule tab, read-only | `P` | `linked-child` | 18 | 🚫 |

**Notes.** Requires `PARENT` in the `ROLES` enum plus `PARENT_STUDENTS (parent_user_id, student_id)` as M:N — WF 05 and WF 17 explicitly require **one parent ↔ many children across multiple instructors**. That cross-instructor reach raises `GAP D13`: what isolation exists between two instructors' data inside one parent account. All five endpoints are read-only; WF 18 states plainly that all four tabs are read-only, with payment the single exception (§5.15).

### 5.17 Notifications & real-time — R22, R23

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/notifications` | Feed. Filter `is_read`; mirrors index `NOTIFICATIONS (user_id, is_read)` | all | `self` | 17 | ⚠️ |
| POST | `/notifications/read` | Bulk mark read | all | `self` | 17 | ✅ |
| GET | `/events` | **SSE stream** — the transport behind every "instantly" promise | all | `self` | 08, 09, 10, 15, 16, 17, 18 | ⚠️ |

**The propagation contract.** `SCOPE §3.C` and the wireframes assert real-time sync on six flows. Each needs a named event on `/events`:

| Trigger endpoint | Event | Lands on |
|---|---|---|
| `POST /live-sessions/{id}/end` | `attendance.saved` | 17 badges, 18 |
| `POST /submissions/{id}/grade` | `submission.graded` | 22, 18 |
| `POST /lessons/{id}/publish`, `POST /assessments/{id}/publish` | `content.published` | 20, 17 |
| `POST`/`PATCH /live-sessions` | `schedule.changed` | 19, 17 |
| `POST /payments` | `fee.paid` | 17 badge clears |
| `POST /fees/{id}/remind` | `notification.created` | 17 |

**Notes.** `GET /notifications` is ⚠️: WF 17 promises "tapping an update deep-links to the specific session or quiz", but `NOTIFICATIONS` has title/message/type only — no `target_type` / `target_id` (`GAP A23`, `C18`). The feed is renderable; the deep-link is not. `/events` is ⚠️ because the mechanism is asserted on seven screens and specified nowhere (`GAP D23`); SSE is the proposal, being one-way and read-only, which is exactly the shape of all six flows. Delivery beyond in-app (email/push) is out of scope (`GAP E20`, `D22`) even though "Send reminder" and a mobile parent app both imply it.

### 5.18 Student portal reads

Students reach curriculum through enrollment, never by browsing courses — hence `/me`.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/me/courses` | Enrolled courses via `STUDENT_GROUPS` | `S` | `own-enrollment` | 19, 20 | ✅ |
| GET | `/me/courses/{courseId}/lessons` | **Published lessons only**, grouped by chapter, with per-lesson progress | `S` | `own-enrollment` | 20 | 🚫 `G3`+`G8` |
| GET | `/me/assessments` | "Due soon" across all enrolled courses, sorted by deadline | `S` | `own-enrollment` | 19 | ✅ |
| GET | `/me/grades` | Recent grades | `S` | `own-enrollment` | 19 | ✅ |
| GET | `/me/schedule` | Next session + join state | `S` | `own-enrollment` | 19 | ⚠️ |

**Notes.** `GET /me/courses/{courseId}/lessons` is doubly blocked: the published/draft filter needs `LESSONS.status` (`G3`) and the `Done` / `In progress` chip needs per-student progress data that does not exist (`G8`, `GAP C5`). It is also where `GAP D2` bites — whether a published material inside a draft lesson is visible.

---

## 6. Screen → endpoint matrix

The checklist for the per-page docs. Each row becomes one `## NN - Screen Name` document in `DEMO`'s format.

| # | Screen | Primary endpoints | Blockers |
|---|---|---|---|
| 01 | Login `s-login` | `POST /auth/login`, `POST /auth/refresh` | `E17` one-role routing |
| 02 | Instructor sign-up `s-signup` | `POST /auth/register`, `GET /plans`, `POST /subscriptions` | `A21`, `G16`, `D20` |
| 03 | Forgot password `s-forgot` | `POST /auth/password/forgot`, `.../reset` | `G5` |
| 04 | TA invite `s-tainvite` | `GET /invites/{token}`, `POST /invites/{token}/accept` | `G4`, `G6` |
| 05 | Parent/student invite `s-familyinvite` | same, role-shaped | `G4`, `G1` |
| 06 | Instructor dashboard `s-idash` | `GET /dashboards/instructor`, `GET /live-sessions?from=today`, `GET /grading/queue` | `C3`, `D18` |
| 07 | Curriculum builder `s-curriculum` | `GET /courses/{id}/tree`, chapter + lesson CRUD, both `PUT .../order`, publish/unpublish | `G3` — **`DEMO` written** |
| 08 | Content & assessment hub `s-content` | materials, recordings, `POST /assessments`, questions, publish | `G7`, `D1`, `B16` |
| 09 | Scheduling `s-calendar` | `GET/POST/PATCH /live-sessions` | `G10` recurrence, `G15` |
| 10 | Class session view `s-session` | `GET /live-sessions/{id}`, `PUT .../attendance`, `POST .../end` | `C14`, `D5` |
| 11 | Roster & performance `s-roster` | `GET /students`, `GET /students/{id}` | `C4`, `C13`, `C16`, `G1` |
| 12 | Fees & revenue `s-fees` | `GET /fees/summary`, `GET /fees`, `POST /fees/{id}/remind` | `G2`, `D19` |
| 13 | Instructor settings `s-isettings` | `GET/PATCH /me/profile`, `GET/PATCH /assistants`, `POST /invites`, `GET /me/subscription` | `G4`, `G6`, `D10` |
| 14 | TA dashboard `s-tadash` | `GET /dashboards/assistant` | `C15`, `G6` |
| 15 | Grading queue `s-grading` | `GET /grading/queue`, `PATCH /submissions/{id}/answers/{aid}`, `POST .../grade` | `C9`, `D9`, `A19` |
| 16 | Attendance taking `s-attendance` | `GET`/`PUT /live-sessions/{id}/attendance` | `G6`, `D25` |
| 17 | Parent home `s-phome` | `GET /me/children`, `GET /notifications` | `G1`, `A23` |
| 18 | Child detail `s-pchild` | `GET /children/{id}` + four tabs, `POST /payments` | `G1`, `G2` |
| 19 | Student dashboard `s-shome` | `GET /dashboards/student`, `GET /me/assessments` | `A15` join window |
| 20 | Lesson & materials `s-lesson` | `GET /me/courses/{id}/lessons`, `GET /materials/{id}/content`, `POST .../views` | `G3`, `G7`, `G8` |
| 21 | Live class `s-liveclass` | `GET /live-sessions/{id}/join`, `POST .../attendance/self` | `G13`, `G15`, `A15` |
| 22 | Quiz taking `s-quiz` | `POST /assessments/{id}/attempts`, `PATCH /attempts/{id}/answers`, `POST .../submit` | `G9`, `A12`, `D17` |
| 23 | Homework submission `s-homework` | `POST /assessments/{id}/submissions`, `PATCH /submissions/{id}` | `G11`, `G12`, `A20` |

**Coverage.** 14 of 23 screens can be documented today at least in part. 9 are blocked end-to-end on a missing entity: **03** (`G5`), **04**, **05** (`G4`), **12**, **18** (`G2`+`G1`), **17** (`G1`), **14** (`C15`), **22** (`G9`), and the read half of **20** (`G3`+`G8`).

---

## 7. What blocks what

Ordered by how many endpoints each gap unblocks.

| Gap | Missing | Unblocks | Endpoints |
|---|---|---|---|
| `G1` | `PARENT` role + `PARENT_STUDENTS` M:N | Screens 05, 11, 17, 18 | 8 |
| `G2` | `ENROLLMENT_FEES` + `PAYMENTS` | Screens 12, 18 | 6 |
| `G4` | `INVITES (token_hash, email, role, scope, expires_at, accepted_at)` | Screens 04, 05, 13 | 5 |
| `G6` | Permission flags on `GROUP_ASSISTANTS` | Screens 04, 13, 14, 15, 16 — and **every `A`-role scope check in this document** | 4 + all TA authorization |
| `G9`+`A12` | `ASSESSMENTS.duration_seconds` + an attempt entity | Screen 22 | 4 |
| `G3` | `LESSONS.status DRAFT/PUBLISHED` | Screens 07, 20 | 3 |
| `G8` | `MATERIAL_VIEWS` / `RECORDED_SESSION_VIEWS` | Screens 11, 20 | 3 |
| `G10` | Recurrence model | Screen 09 — **changes the session-write API shape** | 2, shape-defining |
| `G7` | `MATERIALS.access_mode` (+ `size`, `mime_type` for `A9`) | Screen 08, 20 | 3 |
| `G5` | `PASSWORD_RESET_TOKENS` | Screen 03 | 2 |
| `G11`+`G12` | `is_late` split + re-submission semantics | Screen 23 | 2 |
| `G13` | `PARTIAL` attendance or join/leave timestamps | Screen 21 | 1 |
| `G15` | Meeting provider + external id + webhook | Screens 10, 21 | 1 |
| `G16` | Curriculum enum | Screen 02 | 0 — field only |

`G6` deserves emphasis: it is not one screen's problem. Every row in this document with an `A` in the Roles column is asserting a permission that has nowhere to live.

---

## 8. Error catalog

Codes the per-page docs reference instead of restating rules.

**Cross-branch invariants (`ERD:295-304`) — `422`**

| Code | Raised by |
|---|---|
| `LESSON_COURSE_MISMATCH` | `POST/PATCH /live-sessions` when `lesson_id`'s course ≠ the group's course |
| `RECORDING_SESSION_MISMATCH` | `POST/PATCH /recordings` when the source live session's `lesson_id` ≠ the recording's |
| `ASSESSMENT_COURSE_MISMATCH` | `POST /assessments` when `lesson_id` is outside the group's course |

**CHECK constraints (`ERD:288-294`) — `422`**

| Code | Rule |
|---|---|
| `MEETING_URL_REQUIRED` | `mode = ONLINE` |
| `CLASSROOM_REQUIRED` | `mode = ONSITE` |
| `INVALID_TIME_RANGE` | `scheduled_end > scheduled_start` |
| `INVALID_WATCH_LIMIT` | `max_watch_limit >= 0`, where **0 means unlimited** |

**Uniqueness (`ERD:277-287`) — `409`**

| Code | Constraint |
|---|---|
| `ORDER_INDEX_CONFLICT` | `(course_id, order_index)` / `(chapter_id, order_index)` / `(lesson_id, order_index)` |
| `ATTENDANCE_ALREADY_RECORDED` | `(student_id, live_session_id)` |
| `RECORDING_ALREADY_LINKED` | `recorded_from_live_session_id` is unique |

**Delete policy (`ERD:322-335`) — `409`**

| Code | Rule |
|---|---|
| `GROUP_HAS_HISTORY` | `GROUPS → LIVE_SESSIONS` is `RESTRICT` — archive instead |

**State**

| Code | HTTP | Rule |
|---|---|---|
| `SUBMISSION_LOCKED` | `409` | Re-submit after `GRADED` (WF 23) |
| `ATTEMPT_EXPIRED` | `409` | Answer save after the timer (WF 22) |
| `JOIN_WINDOW_CLOSED` | `409` | Join outside the window (WF 19) |
| `GROUP_AT_CAPACITY` | `409` | Enroll past `max_capacity` |

**Auth**

| Code | HTTP | Note |
|---|---|---|
| `INVALID_CREDENTIALS` | `401` | Never distinguishes unknown email from wrong password |
| `TOKEN_EXPIRED` | `401` | Invite and reset links |
| `INSUFFICIENT_SCOPE` | `403` | Right role, wrong ownership — a TA outside assigned groups |

`POST /auth/password/forgot` returns `202` unconditionally and raises nothing — leaking account existence is the failure mode (WF 03).

---

## 9. Writing order

Each per-page doc follows `DEMO`'s structure: `## NN - Screen Name`, then one `##` block per endpoint with **Method + path**, description, Headers, Body (as a Name/Type/Description table), and Response (fenced, status-coded). Conventions from §1–§3 are inherited, not repeated.

**Wave 1 — fully specifiable, no decisions needed**
07 (extend `DEMO` to the full set: reorder, publish, tree), 10, 11 (partial), 16, 15 (partial), 19, 06 (minus stat cards).

**Wave 2 — one decision each, then specifiable**
08 (needs `G7`, `D1`), 09 (needs `G10` — decide before writing, it changes the shape), 20 (needs `G3`, `G8`), 23 (needs `G11`, `G12`), 22 (needs `G9`, `D17`).

**Wave 3 — blocked on new entities**
03 (`G5`), 04 + 13 (`G4`, `G6`), 05 + 17 + 18 (`G1`), 12 (`G2`), 14 (`C15`), 21 (`G13`, `G15`).

**Before Wave 1 starts, four decisions cost nothing and unblock disproportionately:** confirm section == group (`GAP E1`), confirm term folds into course (`G14`), confirm one group per course per student (`GAP E5`), and name the four dashboard stat cards (`C3`). None require schema work.

**Also note for the implementation pass:** `prisma/schema.prisma` currently holds a placeholder `User` model with `Role { STUDENT, INSTRUCTOR, ADMIN }`, which conflicts with the ERD's `TEACHER, STUDENT, ASSISTANT, ADMIN`. The ERD wins; the schema is rewritten from it.
