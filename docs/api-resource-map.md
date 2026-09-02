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
| `POST /api/lessons/{course-id}` | `POST /api/v1/chapters/{chapterId}/lessons` | `LESSONS.chapter_id` is the FK (`ERD:146-152`). A lesson has no direct course parent; the course is derived through the chapter |
| `GET /api/chapters/{course-id}` returning nested `lessons[]` | keep, as `GET /api/v1/courses/{courseId}/chapters?include=lessons` | The builder (WF 07) needs the whole tree in one call, but the default collection response should not silently nest. Make the expansion explicit |

**Casing:** paths `kebab-case`, JSON fields `snake_case` to mirror the ERD column names (`course_id`, `order_index`, `scheduled_start`). `DEMO` mixes `course_id` and `lesson-id` — `snake_case` wins in bodies, `kebab-case` in paths.

**Identifiers:** all resource ids are UUID v4 strings. `DEMO`'s `"course_id":"fn1o380d"` is placeholder text, not a format decision.

**Timestamps:** ISO-8601 with `Z`, always UTC. Rendering per viewer timezone is a client concern (`GAP D24`).

**Money and scores:** decimal-as-string (`"250.00"`) to avoid float loss. A single implied currency until `GAP C19` is resolved.

---

## 2. Cross-cutting contracts

**Auth.** `Authorization: Bearer <access_token>` on everything except the public endpoints marked `—` in the role column. Access token short-lived; refresh token rotates against `USER_SESSIONS.refresh_token_hash` (`ERD:41-50`). "Remember me" (WF 01) extends refresh lifetime only.

**Role codes used in every table below**

| Code | Role | ERD value |
|---|---|---|
| `I` | Instructor | `TEACHER` |
| `A` | Teaching assistant | `ASSISTANT` |
| `P` | Parent | `PARENT` |
| `S` | Student | `STUDENT` |
| `—` | Public / pre-auth | — |

Role alone never authorizes. Every endpoint additionally applies one **ownership scope**:

| Scope | Rule |
|---|---|
| `own-course` | The resource resolves to a course whose `teacher_id` is the caller |
| `assigned-group` | The caller has a non-revoked `GROUP_ASSISTANTS` row for the group **and** the matching permission flag — `can_take_attendance`, `can_grade`, or `can_upload_solutions` |
| `linked-child` | The caller has a `PARENT_STUDENTS` row for the student |
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

`ERD:1-12` splits the old `SESSIONS` table into two branches. **Paths must never cross them.**

```
CURRICULUM — authored once, cohort-independent
  /courses/{}/chapters/{}/lessons/{} → /materials, /recordings
                                     → /assignments/{} → /submissions

COHORTS — per class instance
  /courses/{}/groups/{} → /live-sessions/{} → /attendance
                        → /quizzes/{}       → /questions, /attempts
```

Consequences:

- **Attendance is never nested under a lesson.** It hangs off a `LIVE_SESSIONS` row only (`ERD:238-244`).
- **Materials and recordings are never nested under a group.** They belong to the lesson and are identical for every group of the course (`GAP E4`).
- **Assignments are curriculum; quizzes are cohorts.** Homework attaches to a lesson and is shared by every group; a quiz is issued to one group with its own clock. They were one entity behind a `type` enum and are now separate roots.
- A student reaches curriculum *through* a group enrollment, which is why the student-facing reads live under `/me/...` and not under `/courses/...`.

---

## 4. Resource inventory

| # | Resource root | Backing entities | Primary screens |
|---|---|---|---|
| R1 | `/auth` | `USERS`, `USER_SESSIONS`, `USER_ROLES` (OTP in cache, not a table) | 01, 02, 03 |
| R2 | `/invites` | `INVITES`, `INVITE_GROUPS` | 04, 05, 13 |
| R3 | `/me` | `USERS`, `TEACHERS`, `STUDENTS` | 13, 19 |
| R4 | `/plans`, `/subscriptions` | `SUBSCRIPTION_PLANS`, `SUBSCRIPTIONS` | 02, 13 |
| R4b | `/subjects` | `SUBJECTS` | 02, 07 |
| R5 | `/courses` | `COURSES`, `SUBJECTS` | 06, 07 |
| R6 | `/chapters` | `CHAPTERS` | 07 |
| R7 | `/lessons` | `LESSONS` | 07, 08, 20 |
| R8 | `/materials` | `MATERIALS` | 08, 20 |
| R9 | `/recordings` | `RECORDED_SESSIONS` | 08, 20 |
| R10 | `/uploads` | — (transport only, `GAP E18`) | 08, 15, 23 |
| R11 | `/groups` | `GROUPS`, `STUDENT_GROUPS`, `GROUP_ASSISTANTS` | 09, 11, 13 |
| R12 | `/assistants` | `GROUP_ASSISTANTS` (scope + three permission flags) | 04, 13 |
| R13 | `/live-sessions` | `LIVE_SESSIONS`, `SESSION_SERIES` | 09, 10, 14, 16, 21 |
| R14 | `/attendance` | `ATTENDANCE` | 10, 16, 21 |
| R15a | `/assignments` | `ASSIGNMENTS`, `ASSIGNMENT_SUBMISSIONS` | 08, 11, 20, 23 |
| R15b | `/quizzes` | `QUIZZES`, `QUIZ_QUESTIONS` | 08, 19, 22 |
| R16 | `/attempts` | `QUIZ_ATTEMPTS`, `QUIZ_ANSWERS` | 15, 22 |
| R17 | `/grading` | `QUIZ_ATTEMPTS` (queue views) | 06, 14, 15 |
| R18 | `/students` | `STUDENTS` + derived aggregates | 11 |
| R19 | `/dashboards` | derived across all | 06, 14, 17, 19 |
| R20 | `/fees`, `/payments` | `ENROLLMENT_FEES`, `PAYMENTS` | 12, 18 |
| R21 | `/children` | `PARENTS`, `PARENT_STUDENTS` | 17, 18 |
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
| POST | `/auth/register` | Instructor self-signup, step 1 of 3. Creates `USERS` + `TEACHERS` + `USER_ROLES(TEACHER)` | `—` | — | 02 | ✅ |
| GET | `/auth/me` | Current user, roles, routing target | all | `self` | all | ✅ |
| POST | `/auth/password/forgot` | Email a 6-digit OTP. **Uniform 202 whether or not the email exists** (`WF 03`). Replaces any live OTP for that user | `—` | — | 03 | ✅ |
| POST | `/auth/password/reset` | `email` + `otp` + new password. No token. Wrong or unknown email both return `401 INVALID_OTP` | `—` | — | 03 | ✅ |
| GET | `/me/profile` | Profile tab | all | `self` | 13, 19 | ✅ |
| PATCH | `/me/profile` | Edit profile (`full_name`, `avatar_url`, `subject_ids`, `curriculum`) | all | `self` | 13, 19 | ✅ |
| GET | `/me/sessions` | Active devices — non-revoked `USER_SESSIONS` | all | `self` | — | ✅ |
| DELETE | `/me/sessions/{sessionId}` | Revoke one device (`is_revoked`) | all | `self` | — | ✅ |

**Notes.** `POST /auth/register` matches WF 02: `full_name` (one field on `USERS`), `subject_ids` (catalog ids into `TEACHER_SUBJECTS`), and `curriculum` (`IGCSE` / `AMERICAN_DIPLOMA` / `BOTH` on `TEACHERS`). The client loads ids from `GET /subjects`. Login `remember_me` is stored on `USER_SESSIONS`.

### 5.2 Invites & onboarding — R2 ✅

Every non-instructor account arrives this way. An invite is a **promise of the rows acceptance will write**. `INVITE_GROUPS` stores which groups; it does **not** carry the three permission flags. For a TA, acceptance copies group ids into `GROUP_ASSISTANTS` with all flags false; the instructor grants capabilities once from WF 13 Edit.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| POST | `/invites` | Issue an invite. Upsert on live `(email, role, issuer)`. `group_ids` for TA/student; `linked_student_id` for parent | `I` `S` | `own-course` / `self` | 13, 05 | ✅ |
| GET | `/invites` | Outstanding invites — the issuer's own | `I` `S` | `own-course` / `self` | 13 | ✅ |
| DELETE | `/invites/{inviteId}` | Rescind. Sets `revoked_at` + `revoked_by_user_id`; the row survives | `I` `S` | `own-course` / `self` | 13 | ✅ |
| GET | `/invite-tokens/{token}` | **Public** preview — inviter name, role, and the scope as prose. Unusable token is `410 INVITE_INVALID` | `—` | — | 04, 05 | ✅ |
| POST | `/invite-tokens/{token}/accept` | Create or attach the account, materialize the scope, return `AuthSession` | `—` | — | 04, 05 | ✅ |

**Note the issuer.** `issued_by_user_id` references `USERS`, not `TEACHERS`, because **a student may issue a parent invite for themselves** — WF 05 says the instructor can invite parent and student together *or* the student can add a parent later from their own settings. Invariant 10 constrains it: a student may issue only `PARENT`, and only with `linked_student_id` equal to themselves.

It is also what WF 04 renders. "Mr. Ahmed invited you as a Teaching Assistant" is a join from the invite to the issuing user, which is why the preview endpoint is specifiable at all.

**The public pair moved off `/invites/{id}`.** `/invites/{inviteId}` and `/invites/{token}` are indistinguishable to a router — a real collision, caught by spec linting. Management stays on `/invites`; the token endpoints live at `/invite-tokens/{token}`, which also cleanly separates the authenticated surface from the public one.

**Acceptance is one transaction** and its shape depends on the role: `ASSISTANT` copies each `INVITE_GROUPS` row into `GROUP_ASSISTANTS` with all three flags **false**; `STUDENT` writes `STUDENT_GROUPS` rows; `PARENT` writes one `PARENT_STUDENTS` row. A spent, revoked or expired token is `410`, never `404` — the recipient followed a real link and deserves to know it is spent. TA action permissions are granted afterwards with `PATCH /assistants/{userId}` (WF 13 Edit), so they are not set on the invite and edited again after join.

**Decided.** Re-invite upserts the live row (200) or creates (201). Rescind is allowed by the issuer, and for a student-issued parent invite also by an instructor of that child. Accept is token-only; `password` creates or verifies. Unusable tokens are `410 INVITE_INVALID`.

**One case the schema handles that is easy to miss.** An invited address may already have an account — a parent already linked to a child under a *different* instructor. Acceptance then **attaches** a new `PARENT_STUDENTS` row to the existing user rather than creating a second account, and `accepted_user_id` records which account it resolved to. This is what makes one parent account across multiple instructors work at all.

### 5.3 Billing — R4

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/plans` | Plan tiers for signup step 2 | `—` | — | 02 | ⚠️ |
| POST | `/subscriptions` | Signup step 3 — payment, creates `SUBSCRIPTIONS` | `I` | `self` | 02 | ⚠️ |
| GET | `/me/subscription` | Billing tab | `I` | `self` | 13 | ✅ |
| PATCH | `/me/subscription` | Change plan / cancel | `I` | `self` | 13 | ⚠️ |

**Notes.** ⚠️ on `/plans`: WF 02 sizes the plan on "student count **and TA seats**" but `SUBSCRIPTION_PLANS` has only `max_students` (`GAP D20`). Payment processing itself is out of scope for the resource API — assume a provider token in the body.

### 5.3b Subjects — R4b

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/subjects` | Catalog for the curriculum filter. `?curriculum=IGCSE` / `AMERICAN_DIPLOMA`; omit for both | `—` | — | 02, 07 | ✅ |

**Notes.** Same display name on both tracks is two rows. The list is already sorted; there is no `order_index` in the JSON. Writes (`POST /auth/register`, `PATCH /me/profile`, `POST /courses`, `PATCH /courses/{id}`) take `subject_id` / `subject_ids` from this list. Mismatch with the teacher's or course's curriculum is `422 SUBJECT_CURRICULUM_MISMATCH`.

### 5.4 Curriculum: courses — R5

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/courses` | Instructor's courses. Filters: `status`, `grade_level` | `I` `A` | `own-course` / `assigned-group` | 06, 07 | ✅ |
| POST | `/courses` | Create course (`title`, `subject_id` from `GET /subjects`, `curriculum`) | `I` | `self` | 02, 07 | ✅ |
| GET | `/courses/{courseId}` | Course header — `{subject_name} — {title}` | `I` `A` | `own-course` | 07 | ✅ |
| PATCH | `/courses/{courseId}` | `title`, `subject_id` / `curriculum`, description, `status` (archive here) | `I` | `own-course` | 07 | ✅ |
| DELETE | `/courses/{courseId}` | Empty `DRAFT` only. Live courses are `ARCHIVED` | `I` | `own-course` | — | ✅ |

**Notes.** `DELETE` is only for an empty draft (no groups) — `409 GROUP_HAS_HISTORY` otherwise. The UI retires a course with `PATCH` `ARCHIVED`. Builder page-load is `GET /courses/{id}/chapters?include=lessons` (no `/tree`). `subject_name` on course reads is a join of `SUBJECTS.name`; writes take `subject_id` only. `title` is the WF 07 header (typically the term).

### 5.5 Curriculum: chapters — R6

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/courses/{courseId}/chapters` | Chapters, `order_index` ascending. `?include=lessons` nests them (this is `DEMO`'s "Get Chapters Related to a Course") | `I` `A` | `own-course` | 07 | ✅ |
| POST | `/courses/{courseId}/chapters` | "+ Add Chapter". `order_index` appends if omitted | `I` | `own-course` | 07 | ✅ |
| GET | `/chapters/{chapterId}` | Single chapter | `I` `A` | `own-course` | 07 | ✅ |
| PATCH | `/chapters/{chapterId}` | "Edit" — title, description | `I` | `own-course` | 07 | ✅ |
| DELETE | `/chapters/{chapterId}` | Cascades; `409 HAS_STUDENT_WORK` if nested homework has submissions | `I` | `own-course` | 07 | ✅ |
| PUT | `/courses/{courseId}/chapters/order` | **Bulk reorder** — body is the full ordered `chapter_id` array. One request per drag-drop | `I` | `own-course` | 07 | ✅ |

**Notes.** `UNIQUE (course_id, order_index)` (`ERD:364-383`) means naive per-item reorder produces transient collisions. The bulk `PUT` reassigns the whole sequence in one transaction — this is why reorder is not a `PATCH` on the item.

### 5.6 Curriculum: lessons — R7

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/chapters/{chapterId}/lessons` | Lessons in order | `I` `A` | `own-course` | 07 | ✅ |
| POST | `/chapters/{chapterId}/lessons` | "+ Add Lesson" — corrects `DEMO`'s `POST /api/lessons/{course-id}` | `I` | `own-course` | 07 | ✅ |
| GET | `/lessons/{lessonId}` | Lesson header for the Content Hub | `I` `A` | `own-course` | 08 | ✅ |
| PATCH | `/lessons/{lessonId}` | Title, description | `I` | `own-course` | 07, 08 | ✅ |
| DELETE | `/lessons/{lessonId}` | Cascades materials + recordings; **`SET NULL` on `LIVE_SESSIONS.lesson_id`** | `I` | `own-course` | 07 | ✅ |
| PUT | `/chapters/{chapterId}/lessons/order` | Bulk reorder within a chapter | `I` | `own-course` | 07 | ✅ |
| POST | `/lessons/{lessonId}/publish` | Draft → Published; makes it visible on WF 20 | `I` | `own-course` | 07 | ✅ |
| POST | `/lessons/{lessonId}/unpublish` | Published → Draft | `I` | `own-course` | 07 | ✅ |

**Notes.** The `DELETE` doc must state the `SET NULL` behaviour explicitly: **deleting a lesson never destroys attendance history** (`ERD:465-496`). A live session that covered the lesson survives with `lesson_id = null`. Publish/unpublish is modelled as a state transition endpoint rather than a `PATCH` field so the real-time fan-out to WF 20 and WF 17 has one hook.

### 5.7 Materials & recordings — R8, R9, R10

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/lessons/{lessonId}/materials` | Files list — name, size, type, access mode | `I` `A` `S` | `own-course` / `own-enrollment` | 08, 20 | ✅ |
| POST | `/lessons/{lessonId}/materials` | Attach an uploaded file. Body sets `access_mode` (view-only / downloadable) | `I` `A` | `own-course` / `assigned-group`+upload | 08 | ✅ |
| PATCH | `/materials/{materialId}` | Rename, change access mode | `I` | `own-course` | 08 | ✅ |
| DELETE | `/materials/{materialId}` | Remove file | `I` | `own-course` | 08 | ✅ |
| GET | `/materials/{materialId}/content` | Issue a short-lived signed URL, honouring `access_mode` | `S` `P` `I` `A` | `own-enrollment` | 20 | ✅ |
| GET | `/lessons/{lessonId}/recordings` | Recordings for a lesson | `I` `A` `S` | as above | 08, 20 | ✅ |
| POST | `/lessons/{lessonId}/recordings` | Add recording — `video_url`, `duration_seconds`, `publish_at`, `deadline`, `max_watch_limit` | `I` | `own-course` | 08 | ✅ |
| PATCH | `/recordings/{recordingId}` | Edit gating fields | `I` | `own-course` | 08 | ✅ |
| DELETE | `/recordings/{recordingId}` | Remove | `I` | `own-course` | 08 | ✅ |
| PUT | `/lessons/{lessonId}/recordings/order` | Bulk reorder | `I` | `own-course` | 08 | ✅ |
| POST | `/uploads` | Request an upload target (signed PUT). Returns `file_url` to pass to the material/recording/submission create | `I` `A` `S` | `self` | 08, 15, 23 | ⚠️ |

**Notes.** `size_bytes` and `mime_type` back WF 08's "1.2 MB" and type icon. `max_watch_limit` is stored on the recording but not enforced — there is no per-student view log.

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
| DELETE | `/groups/{groupId}/students/{studentId}` | Unenroll | `I` | `own-course` | 11 | ✅ |
| GET | `/assistants` | TA list with scope + permissions — the WF 13 table | `I` | `own-course` | 13 | ✅ |
| GET | `/assistants/{userId}` | One TA's groups and flags | `I` | `own-course` | 13 | ✅ |
| PATCH | `/assistants/{userId}` | "Edit" — replace the group set and the three flags in one call | `I` | `own-course` | 13 | ✅ |
| POST | `/assistants/{userId}/revoke` | Set `is_revoked` on every row — access ends, `graded_by_user_id` attribution survives | `I` | `own-course` | 13 | ✅ |

**Notes.** WF 13's two axes both land on `GROUP_ASSISTANTS`: *scope* is which rows exist (chosen at invite), *permissions* are `can_take_attendance` / `can_grade` / `can_upload_solutions`, set **once with Edit after the TA accepts**. "Attendance only" (Omar S.) is one row with one flag set. A newly accepted TA shows "Not set" until that Edit.

**"All sections" is stored as N rows, not a wildcard** — so it does **not** auto-include groups created later. Confirmed (D10): the instructor Edits again when a new section is created.

Revocation is `is_revoked = true`, never a row delete, because `QUIZ_ANSWERS.graded_by_user_id` and `QUIZ_ATTEMPTS.graded_by_user_id` point at that user — `USERS → GROUP_ASSISTANTS` is `RESTRICT` for the same reason (`GAP D31`).

`PATCH /groups/{groupId}` is ⚠️: WF 09 never edits `schedule_info` or `classroom_location` and no screen shows `max_capacity` (`GAP B12`, `B13`). The fields exist; nothing drives them.

### 5.9 Scheduling — R13

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/live-sessions` | **The timetable query.** Filters: `from`, `to`, `group_id`, `course_id`, `mode`, `status`. Mirrors index `LIVE_SESSIONS (group_id, scheduled_start)` | `I` `A` `S` `P` | role-shaped | 09, 06, 14, 19, 18 | ✅ |
| POST | `/live-sessions` | "+ New Session" — one-off, or a `recurrence` block that creates a `SESSION_SERIES` and materializes occurrences | `I` | `own-course` | 09 | ✅ |
| GET | `/live-sessions/{sessionId}` | Session detail for the Class Session View | `I` `A` | `assigned-group` | 10, 16, 21 | ✅ |
| PATCH | `/live-sessions/{sessionId}` | Edit time, room, mode, linked lesson. Query `scope=this` (detach from series) or `scope=this_and_following` | `I` | `own-course` | 09 | ✅ |
| POST | `/live-sessions/{sessionId}/cancel` | Set `status = CANCELLED`. Kept with no screen. Cancelled sessions drop out of attendance % | `I` | `own-course` | — | ✅ |
| GET | `/live-sessions/{sessionId}/join` | Returns the pasted `meeting_url` plus whether the join window is open (`join_opens_minutes_before`) | `S` | `own-enrollment` | 19, 21 | ✅ |
| POST | `/webhooks/meetings/{provider}` | Ingest a provider join log for auto-attendance. **Unused in v1** — no OAuth credentials | `—` | signature | 10, 21 | ⚠️ |

**Notes — recurrence.** Weekly sessions per section write a `SESSION_SERIES` parent and materialized `LIVE_SESSIONS` rows. `PATCH` takes `scope=this` (nulls `series_id` on that occurrence) or `scope=this_and_following` (updates this and later siblings by `scheduled_start`, **skipping any sibling that already has attendance**).

`POST /live-sessions` also carries two CHECK constraints as `422`s: `mode=ONLINE ⇒ meeting_url` required, `mode=ONSITE ⇒ classroom_location` required, plus `scheduled_end > scheduled_start`. And the cross-branch invariant: if `lesson_id` is set, the lesson's course must equal the group's course.

**Pasted URL, not OAuth.** `meeting_url` is copied in by the instructor. The platform does not hold Zoom/Meet credentials, so it cannot mint links or read a join log. `meeting_provider` / `external_meeting_id` wait for a later integration. `/cancel` stays even though WF 09 has no cancel control. Cancelled sessions are **excluded from the attendance denominator**.

### 5.10 Attendance — R14

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/live-sessions/{sessionId}/attendance` | The checkable roster — union of recorded rows and current members. Same API for WF 10 and WF 16 | `I` `A` | `assigned-group`+attendance | 10, 16 | ✅ |
| PUT | `/live-sessions/{sessionId}/attendance` | **Bulk save.** Body is the full status array — this is both "Mark all present" and "Save Attendance" | `I` `A` | `assigned-group`+attendance | 10, 16 | ✅ |
| PATCH | `/attendance/{attendanceId}` | Single-student override | `I` `A` | `assigned-group`+attendance | 10 | ✅ |
| POST | `/live-sessions/{sessionId}/end` | "End Session & Save Attendance" — commits attendance, sets `status = COMPLETED`, **fires the parent-badge fan-out** | `I` `A` | `assigned-group`+attendance | 10 | ✅ |
| POST | `/live-sessions/{sessionId}/attendance/self` | Auto-mark on join from the Live Class screen | `S` | `own-enrollment` | 21 | ✅ |

**Notes.** `GET .../attendance` is recorded `ATTENDANCE` rows **unioned with** current membership (C14). A student who left still appears if they were marked.

`POST .../attendance/self` writes `PRESENT` with `joined_at` and `recorded_by_user_id` null (machine). Leaving early sets `left_at` and may flip status to `PARTIAL`. A later manual `PATCH` wins and stamps `recorded_by_user_id`. Instructor Session View and TA Attendance are the **same endpoints** (D25). Cancelled sessions are not in the attendance-percentage denominator.

### 5.11 Assignments — R15a ✅

Homework lives on the **curriculum branch**: an assignment hangs off a lesson, is authored once, and is seen by every group taking the course. It is checked for on-time submission and never scored; the feedback mechanism is a released solution file the student self-checks against.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/lessons/{lessonId}/assignments` | Homework attached to a lesson | `I` `A` `S` | `own-course` / `own-enrollment` | 08, 20 | ✅ |
| POST | `/lessons/{lessonId}/assignments` | Create — title, description, `due_date`, optional instructions file | `I` | `own-course` | 08 | ✅ |
| GET | `/assignments/{assignmentId}` | Detail — the WF 23 header and deadline | `I` `A` `S` | scoped | 23 | ✅ |
| PATCH | `/assignments/{assignmentId}` | Edit title, description, `due_date` | `I` | `own-course` | 08 | ✅ |
| DELETE | `/assignments/{assignmentId}` | **`409` once submissions exist** — student work is never silently destroyed | `I` | `own-course` | 08 | ✅ |
| PUT | `/lessons/{lessonId}/assignments/order` | Bulk reorder within a lesson | `I` | `own-course` | 08 | ✅ |
| PUT | `/assignments/{assignmentId}/solution` | Upload the solution file — this is WF 15's "+ Upload homework solutions" | `I` `A` | `own-course` / `assigned-group`+upload | 15 | ✅ |
| POST | `/assignments/{assignmentId}/solution/release` | Set `solution_released_at`, making the solution visible to students | `I` `A` | `own-course` / `assigned-group`+upload | 15 | ✅ |
| POST | `/assignments/{assignmentId}/submissions` | Submit — `file_url` + optional `student_note`. Server computes `is_late` against `due_date` | `S` | `own-enrollment` | 23 | ✅ |
| PUT | `/assignments/{assignmentId}/submissions/mine` | Re-submit — **overwrites in place**, per `UNIQUE (assignment_id, student_id)` | `S` | `self` | 23 | ⚠️ |
| GET | `/assignments/{assignmentId}/submissions` | Who handed in, who was late, who is missing | `I` `A` | `own-course` / `assigned-group` | 11 | ✅ |

**Notes.** `due_date` is shared by every section — **decided:** groups keep the same pace, so there is no `GROUP_ASSIGNMENTS` junction.

`PUT .../submissions/mine` is ⚠️ because nothing locks it. WF 23 says re-submission is open "until the instructor grades it" — but there is no grading step for assignments any more, so the lock needs a new trigger. `solution_released_at` is the recommended one (`ERD` Open Question 3): once the answers are public, submission closes.

**There is no grading queue for assignments.** WF 15 is quizzes only. The single homework write a TA makes is the solution upload.

### 5.12 Quizzes — R15b ✅

Quizzes live on the **cohort branch**: issued to one group, with an open/close window and a per-attempt clock.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/quizzes` | Filters: `group_id`, `lesson_id`, `closes_before`, `status`. Mirrors index `QUIZZES (group_id, closes_at)` | `I` `A` `S` | role-shaped | 06, 14, 19 | ✅ |
| POST | `/groups/{groupId}/quizzes` | Create — `opens_at`, `closes_at`, optional `duration_seconds`, `max_attempts` (default 1), `max_score`, optional `lesson_id` tag | `I` | `own-course` | 08 | ✅ |
| GET | `/quizzes/{quizId}` | Detail with questions, for the builder | `I` `A` | `own-course` | 08, 15 | ✅ |
| PATCH | `/quizzes/{quizId}` | Edit window, duration, title, `max_attempts` | `I` | `own-course` | 08 | ✅ |
| DELETE | `/quizzes/{quizId}` | **`409` once attempts exist** | `I` | `own-course` | 08 | ✅ |
| GET | `/quizzes/{quizId}/questions` | Question list in `order_index` order | `I` `A` | `own-course` | 08 | ✅ |
| POST | `/quizzes/{quizId}/questions` | "+ Add Question" — `MCQ` carries `options` + `model_answer`; `STRUCTURED` carries `model_answer` only | `I` | `own-course` | 08 | ✅ |
| PATCH | `/questions/{questionId}` | Edit | `I` | `own-course` | 08 | ✅ |
| DELETE | `/questions/{questionId}` | Remove | `I` | `own-course` | 08 | ✅ |
| PUT | `/quizzes/{quizId}/questions/order` | Bulk reorder — drives the WF 22 navigator | `I` | `own-course` | 08 | ✅ |

**Notes.** Quizzes stay group-scoped. Authoring from a lesson on WF 08 still POSTs `/groups/{groupId}/quizzes` once per section (D1). Assignments are natively lesson-scoped.

Two CHECK constraints surface as `422`: `closes_at > opens_at`, and `duration_seconds > 0` when set (null = untimed). One cross-branch invariant: `lesson_id`, when set, must belong to the group's course.

### 5.13 Quiz attempts — R16 ✅

Student-side. The attempt is the in-flight quiz — what WF 22's countdown and navigator read and write against — and it becomes the graded record on submit. There is no separate submission entity.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| POST | `/quizzes/{quizId}/attempts` | Start. Sets `started_at` and materializes `expires_at` = `min(started_at + duration, closes_at)`. Returns questions | `S` | `own-enrollment` | 22 | ✅ |
| GET | `/attempts/{attemptId}` | Resume — answers so far, seconds remaining, per-question answered flags for the navigator | `S` | `self` | 22 | ✅ |
| PATCH | `/attempts/{attemptId}/answers` | Autosave. Upserts against `UNIQUE (attempt_id, question_id)`. `409 ATTEMPT_EXPIRED` past `expires_at` | `S` | `self` | 22 | ✅ |
| POST | `/attempts/{attemptId}/submit` | Finalize. Auto-scores MCQs into `auto_score`, sets `status = SUBMITTED`. Timer expiry **auto-submits** | `S` | `self` | 22 | ✅ |
| GET | `/attempts/{attemptId}/result` | Student's view after submit: `auto_score` now, `total_score` when grading completes | `S` | `self` | 22 | ✅ |

**Notes.** Timer expiry **auto-submits** (D17) — no grace. The client should POST submit at zero; if it does not, the next student request or a worker runs the same path.

`GET .../result` is where "MCQ score shows immediately; overall grade stays pending until a human grades it" is served: `auto_score` is populated at submit, `total_score` stays null until §5.14 finishes. The response should carry both plus a `grading_status` so the client can render "pending" without inferring it from a null.

`max_attempts` (default 1) is editable. `UNIQUE (quiz_id, student_id, attempt_number)` plus a partial unique on `IN_PROGRESS`. `409 ATTEMPT_IN_PROGRESS` / `ATTEMPT_LIMIT_REACHED`.

### 5.14 Grading queue — R17 ✅

TA-side, and the whole of WF 15. Two facts shape every endpoint here:

- **The queue is a query, not a table.** Pending work is `QUIZ_ANSWERS` where `points_awarded IS NULL`, joined to `QUIZ_QUESTIONS` on `question_type = 'STRUCTURED'`, and to `GROUP_ASSISTANTS` for scope. The partial index `QUIZ_ANSWERS (attempt_id) WHERE points_awarded IS NULL` exists for exactly this.
- **The unit of work is one answer, not one attempt.** WF 15 serves "Youssef T. — Q4 (structured answer)" with its own score box, Save and Skip. `GET /grading/queue/next` takes a soft claim (`claimed_by_user_id`, `claimed_at`) so Skip does not re-serve the same essay.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/grading/queue` | **The dashboard.** Ungraded structured answers across every group the caller may grade. Filters: `quiz_id`, `group_id`, `course_id`. Each item carries student, question text, `points` available, the student's answer, and `model_answer` | `I` `A` | `assigned-group`+`can_grade` | 15 | ✅ |
| GET | `/grading/summary` | Counts for the badges — pending per quiz, and per group. Backs WF 06's "24 pending" and WF 14's tile | `I` `A` | `assigned-group`+`can_grade` | 06, 14, 15 | ✅ |
| GET | `/grading/queue/next` | Serve the next item and take a soft claim (`claimed_by_user_id`, `claimed_at`) | `I` `A` | `assigned-group`+`can_grade` | 15 | ✅ |
| POST | `/grading/queue/{answerId}/skip` | Release the claim and move on. Item returns to the pool | `I` `A` | `assigned-group`+`can_grade` | 15 | ✅ |
| PATCH | `/answers/{answerId}/grade` | **Save.** Writes `points_awarded`, optional `evaluator_comment`, stamps `graded_by_user_id` + `graded_at`. Last structured grade **auto-finalizes** the attempt. Clears any claim | `I` `A` | `assigned-group`+`can_grade` | 15 | ✅ |
| PATCH | `/grading/answers` | **Bulk save.** An array of `{answer_id, points_awarded, evaluator_comment}` | `I` `A` | `assigned-group`+`can_grade` | 15 | ✅ |
| GET | `/quizzes/{quizId}/attempts` | Per-quiz grading view — every attempt with its pending count | `I` `A` | `assigned-group`+`can_grade` | 15 | ✅ |
| POST | `/attempts/{attemptId}/finalize` | Instructor override. Idempotent if already `GRADED`. `409 ATTEMPT_INCOMPLETE` if structured answers remain | `I` `A` | `assigned-group`+`can_grade` | 15 | ✅ |

**Authorization — this is the part that was blocked.** Every row above reads `assigned-group`+`can_grade`, which now resolves to a real check: a `GROUP_ASSISTANTS` row for the caller on the answer's `attempt → quiz → group`, with `can_grade = true` and `is_revoked = false`. The course's owning instructor always passes. A TA with "Attendance only" (WF 13, Omar S.) gets `403 INSUFFICIENT_SCOPE` on all of it. Before `G6` this document was asserting a permission with nowhere to live.

**Four service-layer invariants** (`ERD` Grading invariants 6–9) that each endpoint doc must state:

| Rule | Surfaces as |
|---|---|
| Grader must hold `can_grade` on the answer's group | `403 INSUFFICIENT_SCOPE` |
| `0 ≤ points_awarded ≤ question.points` | `422 POINTS_EXCEED_QUESTION` |
| Only `STRUCTURED` answers are human-graded | `422 NOT_MANUALLY_GRADABLE` on an MCQ |
| An attempt reaches `GRADED` only when every structured answer is scored | `409 ATTEMPT_INCOMPLETE` on premature finalize |

**Auto-finalize.** The last `PATCH .../grade` on an attempt's structured answers flips it to `GRADED` and fires `quiz.graded`. `POST /attempts/{attemptId}/finalize` is an instructor override (idempotent if already graded; `409` if incomplete).

**Claim/skip.** Soft lease on `QUIZ_ANSWERS`. Advisory, expires after a few minutes, never blocks a grade. `GET /grading/queue/next` claims; `POST .../skip` releases.

**What is not here.** Assignments have no grading queue — they are checked for on-time submission and self-checked against a released solution (§5.11). WF 15's "+ Upload homework solutions" is `PUT /assignments/{assignmentId}/solution`, and it needs `can_upload_solutions`, not `can_grade`. `model_answer` is returned to the grader by `GET /grading/queue`, which closes `GAP B17`; `evaluator_comment` now has a visible input, which closes half of `B18`.

### 5.15 Roster & aggregates — R18, R19

Everything here is computed on read (`GAP E11`).

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/students` | The 158-row roster. Filters: `group_id`, `attendance_below`, `homework_status`, `q`. Returns attendance %, last quiz %, homework state | `I` `A` | `own-course` | 11 | ⚠️ |
| GET | `/students/{studentId}` | Detail panel: full attendance history, quiz/homework record, linked parent contact(s) | `I` `A` | `own-course` | 11 | ⚠️ `D33` |
| GET | `/students/{studentId}/attendance` | Per-session history | `I` `A` `P` | scoped | 11, 18 | ✅ |
| GET | `/students/{studentId}/grades` | Graded submissions | `I` `A` `P` | scoped | 11, 18 | ✅ |
| GET | `/dashboards/instructor` | WF 06 — four stat cards, today's sessions, pending-grading count | `I` | `own-course` | 06 | 🚫 `C3` |
| GET | `/dashboards/assistant` | WF 14 — assigned sections, pending count, today's sessions to cover | `A` | `assigned-group` | 14 | 🚫 `C15` |
| GET | `/dashboards/student` | WF 19 — next session + join window, due-soon, recent **quiz** grades, homework status chips (never a homework score) | `S` | `self` | 19 | ✅ |
| GET | `/dashboards/parent` | WF 17 — child cards + activity feed | `P` | `linked-child` | 17 | ✅ |

**Notes.** `GET /students` is ⚠️ on two counts: the `Section` column assumes one group per student, but `STUDENT_GROUPS` is many-to-many (`GAP C13`, `D4`); "Missing" homework is the *absence* of an `ASSIGNMENT_SUBMISSIONS` row past `due_date`. Attendance % **excludes cancelled sessions** from the denominator (D15).

`GET /dashboards/instructor` is 🚫 for a documentation reason, not a data one: **the four stat-card labels are blank placeholder bars in the wireframe source.** Only three deep-link targets are named (roster, courses, schedule); the fourth metric is undefined (`GAP C3`). The endpoint cannot be specified until someone says what the numbers count.

`GET /dashboards/assistant` is 🚫 because `GROUP_ASSISTANTS` assigns a TA to a *group*, not a session — "today's sessions to cover" implies a per-session assignment that does not exist (`GAP C15`).

### 5.16 Fees & payments — R20 ✅

Student → instructor money. Distinct from `SUBSCRIPTIONS` (instructor → platform). `COURSES.fees` seeds `ENROLLMENT_FEES.amount`. One fee row per student per group per monthly period; `PAYMENTS` clears it to `PAID`.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/fees/summary` | "This month", "Outstanding", "Paid on time 91%" | `I` | `own-course` | 12 | ✅ |
| GET | `/fees` | Per-student fee rows: student, section, plan, status | `I` | `own-course` | 12 | ✅ |
| POST | `/fees/{feeId}/remind` | "Send reminder" → notifies the linked parent | `I` | `own-course` | 12 | ✅ |
| GET | `/fees/{feeId}/receipt` | Receipt document | `I` `P` | scoped | 12, 18 | ✅ |
| GET | `/children/{studentId}/fees` | Parent-side fee tab | `P` | `linked-child` | 18 | ✅ |
| POST | `/payments` | Parent pays; clears the overdue badge in real time | `P` | `linked-child` | 18 | ✅ |

**Notes.** "Send reminder" fans out to every linked parent (`GAP D33` still open if the UI stays singular). Receipt is `PAYMENTS.receipt_url`.

### 5.17 Parent portal — R21 ✅

The parent tier is modelled: `PARENT` in the `ROLES` enum, a `PARENTS` profile table alongside `TEACHERS` and `STUDENTS`, and `PARENT_STUDENTS (parent_user_id, student_id)` as a composite-PK junction — many-to-many in both directions, so one parent follows several children **and** one child may be followed by both parents.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/me/children` | The child switcher — one card per linked child with attendance %, average, fee badge | `P` | `linked-child` | 17 | ✅ |
| GET | `/children/{studentId}` | Child header + summary | `P` | `linked-child` | 18 | ✅ |
| GET | `/children/{studentId}/attendance` | Attendance tab, read-only | `P` | `linked-child` | 18 | ✅ |
| GET | `/children/{studentId}/grades` | Grades tab, read-only | `P` | `linked-child` | 18 | ✅ |
| GET | `/children/{studentId}/schedule` | Schedule tab, read-only | `P` | `linked-child` | 18 | ✅ |

**Notes.** The link is deliberately **not** instructor-scoped — a parent with children under two instructors holds one account and one set of link rows (WF 05, WF 17). The instructor boundary is therefore a query-time concern, not a schema one, which is exactly `GAP D13`: what isolation exists between two instructors' data inside one parent account. Two service-layer invariants govern every endpoint here (`ERD:429-435`): a parent reads nothing outside their linked children, and a parent is read-only on academic records. All five endpoints are reads; WF 18 states plainly that all four tabs are read-only, with fee payment the single exception (§5.16).

**One consequence to resolve.** M:N means a child may have several linked parents, but the UI's parent-directed actions are singular — "Send reminder" notifies *the* parent (WF 12), the roster panel shows *the* parent contact (WF 11). Fan out to all links, or designate a primary? Recorded as `GAP D33`; `POST /fees/{feeId}/remind` and `GET /students/{studentId}` both depend on the answer.

### 5.18 Notifications & real-time — R22, R23

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/notifications` | Feed. Filter `is_read`; mirrors index `NOTIFICATIONS (user_id, is_read)` | all | `self` | 17 | ⚠️ |
| POST | `/notifications/read` | Bulk mark read | all | `self` | 17 | ✅ |
| GET | `/events` | **SSE stream** — the transport behind every "instantly" promise | all | `self` | 08, 09, 10, 15, 16, 17, 18 | ⚠️ |

**The propagation contract.** `SCOPE §3.C` and the wireframes assert real-time sync on six flows. Each needs a named event on `/events`:

| Trigger endpoint | Event | Lands on |
|---|---|---|
| `POST /live-sessions/{id}/end` | `attendance.saved` | 17 badges, 18 |
| Last structured `PATCH /answers/{id}/grade` (or `POST /attempts/{id}/finalize`) | `quiz.graded` | 22, 18 |
| `POST /lessons/{id}/publish`, `POST /assignments/{id}/solution/release` | `content.published` | 20, 17 |
| `POST`/`PATCH /live-sessions` | `schedule.changed` | 19, 17 |
| `POST /payments` | `fee.paid` | 17 badge clears |
| `POST /fees/{id}/remind` | `notification.created` | 17 |

**Notes.** `GET /notifications` is ⚠️: WF 17 promises "tapping an update deep-links to the specific session or quiz", but `NOTIFICATIONS` has title/message/type only — no `target_type` / `target_id` (`GAP A23`, `C18`). The feed is renderable; the deep-link is not. `/events` is ⚠️ because the mechanism is asserted on seven screens and specified nowhere (`GAP D23`); SSE is the proposal, being one-way and read-only, which is exactly the shape of all six flows. Delivery beyond in-app (email/push) is out of scope (`GAP E20`, `D22`) even though "Send reminder" and a mobile parent app both imply it.

### 5.19 Student portal reads

Students reach curriculum through enrollment, never by browsing courses — hence `/me`.

| Method | Path | Purpose | Roles | Scope | WF | St |
|---|---|---|---|---|---|---|
| GET | `/me/courses` | Enrolled courses via `STUDENT_GROUPS` | `S` | `own-enrollment` | 19, 20 | ✅ |
| GET | `/me/courses/{courseId}/lessons` | **Published lessons only**, grouped by chapter. `progress` is always `null` | `S` | `own-enrollment` | 20 | ✅ |
| GET | `/me/assignments` | Homework due soon across all enrolled courses | `S` | `own-enrollment` | 19, 23 | ✅ |
| GET | `/me/quizzes` | Quizzes open or opening soon, by `closes_at` | `S` | `own-enrollment` | 19, 22 | ✅ |
| GET | `/me/grades` | Recent grades | `S` | `own-enrollment` | 19 | ✅ |
| GET | `/me/schedule` | Next session + join state | `S` | `own-enrollment` | 19 | ✅ |

**Notes.** Published/draft is `LESSONS.status`. There is no per-student view log, so progress chips are not backed. A published material inside a draft lesson is **not** visible — publish gating is at the lesson (`GAP D2`).

---

## 6. Screen → endpoint matrix

The checklist for the per-page docs. Each row becomes one `## NN - Screen Name` document in `DEMO`'s format.

| # | Screen | Primary endpoints | Blockers |
|---|---|---|---|
| 01 | Login `s-login` | `POST /auth/login`, `POST /auth/refresh` | `E17` one-role routing |
| 02 | Instructor sign-up `s-signup` | `GET /subjects`, `POST /auth/register`, `GET /plans`, `POST /subscriptions` | — |
| 03 | Forgot password `s-forgot` | `POST /auth/password/forgot`, `POST /auth/password/reset` | — OTP in cache |
| 04 | TA invite `s-tainvite` | `GET /invite-tokens/{token}`, `POST /invite-tokens/{token}/accept` | `D39` |
| 05 | Parent/student invite `s-familyinvite` | same, role-shaped; student-issued parent invites use `POST /invites` | `D39` |
| 06 | Instructor dashboard `s-idash` | `GET /dashboards/instructor`, `GET /live-sessions?from=today`, `GET /grading/queue` | `C3` |
| 07 | Curriculum builder `s-curriculum` | `GET /courses/{id}/chapters?include=lessons`, chapter + lesson CRUD, both `PUT .../order`, publish/unpublish | — |
| 08 | Content & assessment hub `s-content` | materials, recordings, `POST /lessons/{id}/assignments`, `POST /groups/{id}/quizzes`, questions | — |
| 09 | Scheduling `s-calendar` | `GET/POST/PATCH /live-sessions` | — |
| 10 | Class session view `s-session` | `GET /live-sessions/{id}`, `GET`/`PUT .../attendance`, `POST .../end` | — |
| 11 | Roster & performance `s-roster` | `GET /students`, `GET /students/{id}` | `C4`, `C13`, `D33` |
| 12 | Fees & revenue `s-fees` | `GET /fees/summary`, `GET /fees`, `POST /fees/{id}/remind` | `D33` which parent |
| 13 | Instructor settings `s-isettings` | `GET/PATCH /me/profile`, `GET/PATCH /assistants`, `POST /assistants/{id}/revoke`, `POST`/`GET`/`DELETE /invites`, `GET /me/subscription` | — |
| 14 | TA dashboard `s-tadash` | `GET /dashboards/assistant`, `GET /grading/summary` | `C15` |
| 15 | Grading queue `s-grading` | `GET /grading/queue`, `GET /grading/queue/next`, `POST .../skip`, `PATCH /answers/{id}/grade`, `PATCH /grading/answers`, `POST /attempts/{id}/finalize`, `PUT /assignments/{id}/solution` | `D9` regrade |
| 16 | Attendance taking `s-attendance` | `GET`/`PUT /live-sessions/{id}/attendance` (same as WF 10) | — |
| 17 | Parent home `s-phome` | `GET /me/children`, `GET /notifications` | — |
| 18 | Child detail `s-pchild` | `GET /children/{id}` + four tabs, `POST /payments` | — |
| 19 | Student dashboard `s-shome` | `GET /dashboards/student`, `GET /me/assignments`, `GET /me/quizzes` | — |
| 20 | Lesson & materials `s-lesson` | `GET /me/courses/{id}/lessons`, `GET /materials/{id}/content` | — |
| 21 | Live class `s-liveclass` | `GET /live-sessions/{id}/join`, `POST .../attendance/self` | — |
| 22 | Quiz taking `s-quiz` | `POST /quizzes/{id}/attempts`, `PATCH /attempts/{id}/answers`, `POST .../submit` | — |
| 23 | Homework submission `s-homework` | `POST /assignments/{id}/submissions`, `PUT .../submissions/mine` | OQ3 lock |

**Coverage.** Entity gaps G1–G16 that blocked endpoints are closed except behavioural leftovers (`C3` dashboard labels, `C15` per-session TA cover, OQ3 assignment resubmit lock). Screen **14**'s "sessions to cover" tile is still 🚫. Meeting webhook is ⚠️ until provider credentials exist.

---

## 7. What blocks what

Ordered by how many endpoints each gap unblocks.

| Gap | Missing | Unblocks | Endpoints |
|---|---|---|---|
| ~~`G1`~~ | ✅ **Resolved** — `PARENT` role, `PARENTS`, `PARENT_STUDENTS` M:N | Screens 05, 11, 17, 18 | 8 unblocked |
| ~~`G9`+`A12`~~ | ✅ **Resolved** — `QUIZZES.opens_at/closes_at/duration_seconds` + `QUIZ_ATTEMPTS` | Screen 22 | 4 unblocked |
| ~~`G11`+`G12`~~ | ✅ **Resolved** — `ASSIGNMENT_SUBMISSIONS.is_late` boolean; re-submit overwrites in place | Screen 23 | 2 unblocked |
| ~~`A19`+`A20`~~ | ✅ **Resolved** — `ASSIGNMENTS.solution_file_url`, `ASSIGNMENT_SUBMISSIONS.student_note` | Screens 15, 23 | 2 unblocked |
| ~~`G4`~~ | ✅ **Resolved** — `INVITES` + `INVITE_GROUPS`, issuer on `USERS` so students can invite parents | Screens 04, 05, 13 | 5 unblocked |
| ~~`G6`~~ | ✅ **Resolved** — `can_take_attendance` / `can_grade` / `can_upload_solutions` + `is_revoked` on `GROUP_ASSISTANTS`. Flags are granted after invite acceptance, not copied from `INVITE_GROUPS` | Screens 04, 13, 14, 15, 16 — and **every `A`-role check in this document** | 4 + all TA authorization |
| **OQ1** | ~~Per-group assignment deadline~~ **Decided: shared `due_date`.** Sections keep the same pace; no `GROUP_ASSIGNMENTS` | Screens 08, 23 | — |
| ~~`G2`~~ | ✅ `ENROLLMENT_FEES` + `PAYMENTS` | Screens 12, 18 | 6 unblocked |
| ~~`G3`~~ | ✅ `LESSONS.status DRAFT/PUBLISHED` | Screens 07, 20 | 3 unblocked |
| `G8` | **Dropped.** No `MATERIAL_VIEWS` / `RECORDED_SESSION_VIEWS`. Roster "viewed" and watch-limit enforcement are out of schema | Screens 11, 20 | — |
| ~~`G10`~~ | ✅ `SESSION_SERIES` parent; occurrences materialized; `PATCH ?scope=` | Screen 09 | 2 unblocked |
| ~~`G7`~~ | ✅ `MATERIALS.access_mode`, `size_bytes`, `mime_type` | Screen 08, 20 | 3 unblocked |
| ~~`G5`~~ | ✅ **Resolved** — password-reset OTP in **cache**, not a table | Screen 03 | 2 unblocked |
| ~~`G13`~~ | ✅ `PARTIAL` + `joined_at` / `left_at` / `recorded_by_user_id` | Screen 21 | 1 unblocked |
| ~~`G15`~~ | ✅ Fields exist. **v1 pastes `meeting_url`**; webhook unused until OAuth credentials | Screens 10, 21 | join ready; webhook ⚠️ |
| `G16` | Curriculum enum | Screen 02 | 0 — field only |

`G6` was the one that mattered most: every row in this document with an `A` in the Roles column was asserting a permission that had nowhere to live. With the three flags on `GROUP_ASSISTANTS`, `assigned-group` is now a check the service layer can actually run.

---

## 8. Error catalog

Codes the per-page docs reference instead of restating rules.

**Cross-branch invariants (`ERD:398-407`) — `422`**

| Code | Raised by |
|---|---|
| `LESSON_COURSE_MISMATCH` | `POST/PATCH /live-sessions` when `lesson_id`'s course ≠ the group's course |
| `RECORDING_SESSION_MISMATCH` | `POST/PATCH /recordings` when the source live session's `lesson_id` ≠ the recording's |
| `QUIZ_COURSE_MISMATCH` | `POST /groups/{id}/quizzes` when the `lesson_id` tag is outside the group's course |

**CHECK constraints (`ERD:384-397`) — `422`**

| Code | Rule |
|---|---|
| `MEETING_URL_REQUIRED` | `mode = ONLINE` |
| `CLASSROOM_REQUIRED` | `mode = ONSITE` |
| `INVALID_TIME_RANGE` | `scheduled_end > scheduled_start` |
| `INVALID_WATCH_LIMIT` | `max_watch_limit >= 0`, where **0 means unlimited** |
| `INVALID_QUIZ_WINDOW` | `closes_at > opens_at` |
| `INVALID_QUIZ_DURATION` | `duration_seconds > 0` when set |
| `INVALID_MAX_ATTEMPTS` | `max_attempts >= 1` |
| `SOLUTION_BEFORE_DEADLINE` | `solution_released_at >= due_date` |

**Uniqueness (`ERD:364-383`) — `409`**

| Code | Constraint |
|---|---|
| `ORDER_INDEX_CONFLICT` | `(course_id, order_index)` / `(chapter_id, order_index)` / `(lesson_id, order_index)` |
| `ATTENDANCE_ALREADY_RECORDED` | `(student_id, live_session_id)` |
| `ATTEMPT_IN_PROGRESS` | Partial unique: one `IN_PROGRESS` attempt per student per quiz |
| `ATTEMPT_LIMIT_REACHED` | Count of attempts ≥ `max_attempts` |
| `RECORDING_ALREADY_LINKED` | `recorded_from_live_session_id` is unique |

**Delete policy (`ERD:465-496`) — `409`**

| Code | Rule |
|---|---|
| `GROUP_HAS_HISTORY` | `GROUPS → LIVE_SESSIONS` and `GROUPS → QUIZZES` are `RESTRICT` — archive instead |
| `HAS_STUDENT_WORK` | `ASSIGNMENTS → ASSIGNMENT_SUBMISSIONS` and `QUIZZES → QUIZ_ATTEMPTS` are `RESTRICT` |

**State**

| Code | HTTP | Rule |
|---|---|---|
| `SUBMISSION_LOCKED` | `409` | Re-submit after the solution is released (WF 23) — trigger pending `ERD` Open Question 3 |
| `ATTEMPT_EXPIRED` | `409` | Answer save after the timer (WF 22) |
| `POINTS_EXCEED_QUESTION` | `422` | `points_awarded > question.points` |
| `NOT_MANUALLY_GRADABLE` | `422` | Human grade attempted on an `MCQ` answer |
| `ATTEMPT_INCOMPLETE` | `409` | Finalize before every structured answer is scored |
| `JOIN_WINDOW_CLOSED` | `409` | Join outside the window (WF 19) |
| `GROUP_AT_CAPACITY` | `409` | Enroll past `max_capacity` |

**Auth**

| Code | HTTP | Note |
|---|---|---|
| `INVALID_CREDENTIALS` | `401` | Never distinguishes unknown email from wrong password |
| `TOKEN_EXPIRED` | `401` | Invite links |
| `INVALID_OTP` | `401` | Wrong reset code, or no matching account — never distinguished |
| `OTP_EXPIRED` | `410` | Reset code expired, already used, or locked after too many attempts |
| `INSUFFICIENT_SCOPE` | `403` | Right role, wrong ownership or missing permission flag — a TA outside assigned groups, or one without `can_grade` hitting the queue |

`POST /auth/password/forgot` returns `202` unconditionally and raises nothing — leaking account existence is the failure mode (WF 03).

---

## 9. Published documentation

This map is the working source. The **published** GitBook documentation generated from it lives in
`docs/api/`:

| File | Role |
|---|---|
| `docs/api/openapi.yaml` | OpenAPI 3.1 spec — 141 operations, 108 schemas. The machine-readable contract |
| `docs/api/SUMMARY.md` | GitBook navigation |
| `docs/api/concepts/` | Conventions, roles and scopes, the two branches, errors, real-time, status |
| `docs/api/reference/` | One page per resource group, embedding `{% openapi %}` blocks |

The spec is generated, not hand-edited. When the ERD or this map changes, regenerate rather than
patching `openapi.yaml` directly.

## 10. Writing order

Each per-page doc follows `DEMO`'s structure: `## NN - Screen Name`, then one `##` block per endpoint with **Method + path**, description, Headers, Body (as a Name/Type/Description table), and Response (fenced, status-coded). Conventions from §1–§3 are inherited, not repeated.

**Wave 1 — fully specifiable, no decisions needed**
07 (extend `DEMO` to the full set: reorder, publish, tree), 10, 11 (partial), 15, 16, 22, 19 (minus the homework grade), 06 (minus stat cards), 17 and 18 (minus fees).

**Wave 2 — one decision each, then specifiable**
08 (quiz group pick `D1`), 09 (`D14` this-and-following with attendance), 22 (`D17` expiry), 23 (OQ3 lock).

**Wave 3 — remaining non-entity gaps**
06 (`C3` unnamed stat cards), 14 (`C15` per-session TA cover).

**Moved up by the `G4` resolution:** 04, 05 and 13 join Wave 2 — each needs one invite decision (`D39` email match, `D40` rescind authority) but nothing structural.

**Moved up by the `G1` resolution:** 17 and 18 join Wave 1 for their attendance, grades and schedule surfaces; only their fee tabs wait on `G2`.

**Before Wave 1 starts, three decisions cost nothing and unblock disproportionately:** confirm section == group (`GAP E1`), confirm one group per course per student (`GAP E5`), and name the four dashboard stat cards (`C3`). None require schema work.

**One decision now costs nothing and prevents rework:** none on OQ1 — shared deadline is decided.

**Also note for the implementation pass:** `prisma/schema.prisma` currently holds a placeholder `User` model with `Role { STUDENT, INSTRUCTOR, ADMIN }`, which conflicts with the ERD's `TEACHER, STUDENT, ASSISTANT, ADMIN`. The ERD wins; the schema is rewritten from it.
