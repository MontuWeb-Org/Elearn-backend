# E-Learning Platform — API Documentation (v1.0)

Companion to `elearning-platform-wireframes.html` (23 screens, 4 personas) and the platform ERD.
This document specifies the REST API needed to power every screen and every navigation branch described in the wireframes, mapped directly to the ERD entities.

---

## 0. How to read this document

- Each endpoint is tagged with the **screen(s)** it powers (e.g. `[07]`) so it's traceable back to the wireframe.
- Sections marked **[EXTENSION]** or **[NEW TABLE]** are places where the wireframes require data the provided ERD doesn't model. I've filled these gaps with the minimum addition needed and flagged them — see §3 for the full list and reasoning. Everything else maps 1:1 to the ERD you supplied.
- All other endpoints use only the tables/fields already in your ERD.

---

## 1. Conventions

**Base URL:** `https://api.<domain>.com/api/v1`

**Auth:** Bearer JWT in `Authorization: Header`. Access tokens are short-lived (15 min); refresh via `POST /auth/refresh` using the refresh token issued at login (backed by `USER_SESSIONS`).

```
Authorization: Bearer <access_token>
```

**Content type:** `application/json` for all requests/responses except file uploads (`multipart/form-data`) and signed download redirects.

**IDs:** UUID v4 strings everywhere, matching the ERD's `uuid` PK/FK columns.

**Timestamps:** ISO-8601 UTC, e.g. `2026-08-31T10:00:00Z`.

**Pagination** (list endpoints):
```
GET /resource?page=1&limit=20
```
```json
{
  "data": [ /* items */ ],
  "meta": { "page": 1, "limit": 20, "total": 158, "total_pages": 8 }
}
```

**Errors:**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Course not found or you don't have access to it.",
    "details": {}
  }
}
```
Standard HTTP status codes throughout (`400`, `401`, `403`, `404`, `409`, `422`, `429`, `500`). See §9 for the full code table.

**Role gate notation:** every endpoint lists **Access:** with one or more of `instructor`, `ta`, `parent`, `student`, or `public` (no auth). Where a role's access is *scoped* (e.g. a TA only sees assigned groups), that scoping rule is stated explicitly — it's enforced server-side by joining through `GROUP_ASSISTANTS` / `STUDENT_GROUPS`, never trusted from the client.

---

## 2. Roles & access model

`ROLES` × `USER_ROLES` gives a user→role many-to-many, but the product behaves as **one primary role per account** (login routes by resolved role — screen **01**, note 1). The schema stays many-to-many so a future case (e.g. an instructor who is also a parent on another instructor's platform) doesn't require a migration; today, every account provisioning path (signup, TA invite, family invite) assigns exactly one role.

| Role | Root of hierarchy? | Created via | Scope |
|---|---|---|---|
| `instructor` | Yes — root account | Self-signup (`02`) | Owns courses, groups, TAs, students, fees |
| `ta` | No | Instructor invite (`04`, `13`) | Delegated to specific groups, with specific permissions (§3.3) |
| `parent` | No | Instructor-triggered invite, linked to a student (`05`) | Read-only, scoped to their linked children |
| `student` | No | Instructor-triggered invite (`05`) | Own enrollment, own submissions |

**Enforcement pattern:** every scoped endpoint resolves the caller's accessible resource set server-side:
- `instructor` → `COURSES.teacher_id = current_user`
- `ta` → `GROUP_ASSISTANTS.assistant_user_id = current_user` → reachable `GROUPS`/`COURSES`
- `student` → `STUDENT_GROUPS.student_id = current_user` → reachable `GROUPS`/`COURSES`
- `parent` → `PARENT_STUDENTS.parent_user_id = current_user` (§3.1) → reachable students

---

## 3. Assumptions & schema extensions

The wireframes describe a few flows the supplied ERD doesn't have tables for. Rather than leave gaps, I designed the minimum extension for each and flagged it below. **These are the things worth confirming with you before implementation** — everything else in this doc is a direct mapping of your ERD.

### 3.1 `PARENT_STUDENTS` — **[NEW TABLE]**
The ERD's `STUDENTS` table only has a `parent_phone` string — there's no relational link. But screen **17**'s notes explicitly say *"One parent account can be linked to multiple children/instructors"*, and Parent Home renders a list of children. A string field can't model that. Proposed table:

```
PARENT_STUDENTS {
  uuid  parent_id PK, FK → USERS.id
  uuid  student_id PK, FK → STUDENTS.user_id
  string relationship_label   -- optional, e.g. "Mother"
  timestamp linked_at
}
```
`STUDENTS.parent_phone` is kept as a display/contact convenience field, not the source of truth for the relationship.

### 3.2 `INVOICES` — **[NEW TABLE]**
`SUBSCRIPTION_PLANS`/`SUBSCRIPTIONS` in the ERD are the **instructor's own platform billing** (max_students, seat pricing — this is what screen **02** step 2 sets up). They aren't the same thing as screen **12** (Fees & Revenue) and the parent's Fees tab on screen **18**, which track *a student's payment status for a course*. There's no table for that in the ERD, so:

```
INVOICES {
  uuid       invoice_id PK
  uuid       student_id FK → STUDENTS.user_id
  uuid       course_id  FK → COURSES.course_id
  string     billing_period        -- e.g. "August 2026"
  decimal    amount
  enum       status                -- pending | paid | overdue
  timestamp  due_date
  timestamp  paid_at
  string     payment_method
  string     receipt_url
  timestamp  created_at
}
```
`COURSES.fees` is the default amount used when an invoice is generated; `INVOICES.amount` can be overridden per-student (discounts, proration).

### 3.3 `GROUP_ASSISTANTS.permissions` — **[EXTENSION]**
Screen **13** shows per-TA permission toggles ("Attendance only" vs "Grading, Attendance"), but the ERD's `GROUP_ASSISTANTS` is a bare composite key (`assistant_user_id`, `group_id`) with no permission granularity. Extending it with one column avoids a whole new join table:

```
GROUP_ASSISTANTS {
  uuid  assistant_user_id PK, FK
  uuid  group_id PK, FK
  string[] permissions   -- subset of: attendance, grading, homework_upload   [EXTENSION]
}
```

### 3.4 `ASSESSMENT_QUESTIONS.question_type` gains `file_upload` — **[CLARIFICATION]**
Screens **08/22/23** treat Quiz and Homework as different experiences (MCQ list vs. a single file drop), but they map cleanly onto the *same* `ASSESSMENTS` / `ASSESSMENT_QUESTIONS` / `ASSESSMENT_SUBMISSIONS` tables already in your ERD if homework is modeled as an assessment (`type = homework`) with one question of `question_type = file_upload`, answered via `ASSESSMENT_SUBMISSION_ANSWERS.file_url`. No new table — just one more enum value.

### 3.5 `MATERIALS.assessment_id` (nullable) — **[EXTENSION]**
Screen **15**'s "+ Upload homework solutions" needs somewhere to store the solution file. `MATERIALS` is currently lesson-scoped only. Adding a nullable `assessment_id` lets a solution file attach to an assessment directly, released to students only after grading closes, without a new table.

### 3.6 Group/section creation has no dedicated screen — **[FLOW GAP]**
None of the 23 screens shows a "create group" UI, but `GROUPS` sits between `COURSES` and everything that references it (`STUDENT_GROUPS`, `GROUP_ASSISTANTS`, `LIVE_SESSIONS`, `ASSESSMENTS` all FK to `group_id`), so it has to be created before enrollment, TA assignment, or scheduling can happen. The required order is:

**course (07) → group/section (no screen — see below) → students (05) / TAs (13), either order → sessions (09) / assessments (08)**

`POST /courses/{id}/groups` (§6.7) is the endpoint; I'd suggest surfacing it either as a "Sections" tab next to the chapter tree on screen **07**, or inline in screen **09**'s "+ New Session" flow (create-a-group-if-none-exists) — screen 09 is the first place a group is actually required. Worth deciding which before this gets built, since it changes where that UI lives.

### 3.7 Real-time sync
The notes use "instantly", "real time" repeatedly (schedule → student/parent, attendance → parent, grades → parent, fee payment → parent badge). I've documented every write endpoint that triggers a sync, and added a lightweight WebSocket channel (§8) for pushing those events; every one of them is also reflected in `NOTIFICATIONS`, so a client that isn't connected to the socket still catches up via `GET /notifications` / polling. If you'd rather not build a socket layer for v1, all "real-time" behavior degrades gracefully to polling `GET /notifications` — nothing else in the API depends on the socket existing.

**Please confirm 3.1–3.5** — they're the only places I've designed beyond what you gave me. Everything from §4 onward assumes these are in place.

---

## 4. Data model reference

Quick field reference per table, ERD field names preserved exactly. New/extended fields are marked. Skip to §6 if you just want the endpoints.

<details>
<summary><b>Identity & access</b> — USERS, ROLES, USER_ROLES, USER_SESSIONS, TEACHERS, STUDENTS, PARENT_STUDENTS†</summary>

```
USERS(id, email, password_hash, first_name, last_name, age, is_active, date_joined, last_login_at)
ROLES(role_id, name)                          -- enum: instructor | ta | parent | student
USER_ROLES(user_id, role_id)
USER_SESSIONS(user_session_id, user_id, refresh_token_hash, user_agent, ip_address, is_revoked, expires_at, created_at)
TEACHERS(user_id, bio, specialization, curriculum[])
STUDENTS(user_id, student_code, school_name, parent_phone, grade_level)
PARENT_STUDENTS†(parent_id, student_id, relationship_label, linked_at)     -- † new, §3.1
```
</details>

<details>
<summary><b>Curriculum</b> — COURSES, CHAPTERS, LESSONS, RECORDED_SESSIONS, MATERIALS</summary>

```
COURSES(course_id, teacher_id, course_code, course_name, description, grade_level, curriculum, fees, status)
  status: draft | published | archived
CHAPTERS(chapter_id, course_id, chapter_title, description, order_index)
LESSONS(lesson_id, chapter_id, title, description, order_index, status)     -- status: draft | published
RECORDED_SESSIONS(recorded_session_id, lesson_id, recorded_from_live_session_id, title, video_url,
                   duration_seconds, order_index, max_watch_limit, publish_at, deadline, created_at)
MATERIALS(material_id, lesson_id, assessment_id‡, title, file_url, uploaded_at)   -- ‡ new nullable col, §3.5
```
</details>

<details>
<summary><b>Groups & scheduling</b> — GROUPS, GROUP_ASSISTANTS, STUDENT_GROUPS, LIVE_SESSIONS, ATTENDANCE</summary>

```
GROUPS(group_id, course_id, group_name, schedule_info, classroom_location, max_capacity)
GROUP_ASSISTANTS(assistant_user_id, group_id, permissions‡)     -- ‡ new col, §3.3
STUDENT_GROUPS(student_id, group_id)
LIVE_SESSIONS(live_session_id, group_id, lesson_id, title, mode, meeting_url, classroom_location,
               scheduled_start, scheduled_end, status, created_at)
  mode: online | offline    status: scheduled | live | completed | cancelled
ATTENDANCE(id, student_id, live_session_id, status, recorded_at)
  status: present | absent | late | excused
```
</details>

<details>
<summary><b>Assessments</b> — ASSESSMENTS, ASSESSMENT_QUESTIONS, ASSESSMENT_SUBMISSIONS, ASSESSMENT_SUBMISSION_ANSWERS</summary>

```
ASSESSMENTS(assessment_id, group_id, lesson_id, title, type, max_score, due_date)
  type: quiz | homework
ASSESSMENT_QUESTIONS(question_id, assessment_id, question_text, question_type, options, model_answer, points)
  question_type: mcq | structured | file_upload‡     -- ‡ new enum value, §3.4
ASSESSMENT_SUBMISSIONS(submission_id, assessment_id, student_id, graded_by_user_id, total_score,
                        feedback_comments, status, submitted_at, graded_at)
  status: in_progress | submitted | late | graded
ASSESSMENT_SUBMISSION_ANSWERS(answer_id, submission_id, question_id, student_answer, file_url,
                               points_awarded, evaluator_comment)
```
</details>

<details>
<summary><b>Billing</b> — SUBSCRIPTION_PLANS, SUBSCRIPTIONS (instructor platform billing), INVOICES† (student course fees)</summary>

```
SUBSCRIPTION_PLANS(plan_id, name, max_students, price, billing_period)
SUBSCRIPTIONS(subscription_id, user_id, plan_id, status, start_date, end_date)
  status: pending | active | past_due | cancelled
INVOICES†(invoice_id, student_id, course_id, billing_period, amount, status, due_date, paid_at,
          payment_method, receipt_url, created_at)                          -- † new, §3.2
  status: pending | paid | overdue
```
</details>

<details>
<summary><b>Notifications</b> — NOTIFICATIONS</summary>

```
NOTIFICATIONS(notification_id, user_id, title, message, type, is_read, created_at)
  type: session_reminder | grade_posted | attendance_alert | fee_reminder | invite | announcement
```
</details>

---

## 5. Endpoint index

| # | Method & Path | Access | Screens |
|---|---|---|---|
| 1 | `POST /auth/login` | public | 01 |
| 2 | `POST /auth/refresh` | public (refresh token) | — |
| 3 | `POST /auth/logout` | any | — |
| 4 | `POST /auth/forgot-password` | public | 03 |
| 5 | `POST /auth/reset-password` | public | 03 |
| 6 | `POST /auth/signup/instructor` | public | 02 |
| 7 | `POST /instructor/subscription` | instructor | 02 |
| 8 | `POST /subscriptions/{id}/checkout` | instructor | 02 |
| 9 | `GET /invites/{token}` | public | 04, 05 |
| 10 | `POST /invites/{token}/accept` | public | 04, 05 |
| 11 | `GET /me` | any | all |
| 12 | `PATCH /me` | any | 13 |
| 13 | `GET /notifications` | any | 17, 06 |
| 14 | `PATCH /notifications/{id}/read` | any | — |
| 15 | `GET /instructor/dashboard` | instructor | 06 |
| 16 | `GET /courses` | instructor, student | 06, 07, 19 |
| 17 | `POST /courses` | instructor | 07 |
| 18 | `GET /courses/{id}` | instructor, ta, student, parent | 07, 20 |
| 19 | `PATCH /courses/{id}` | instructor | 07 |
| 20 | `DELETE /courses/{id}` | instructor | 07 |
| 21 | `GET /courses/{id}/curriculum` | instructor, ta, student, parent | 07, 20 |
| 22 | `POST /courses/{id}/chapters` | instructor | 07 |
| 23 | `PATCH /chapters/{id}` | instructor | 07 |
| 24 | `DELETE /chapters/{id}` | instructor | 07 |
| 25 | `PATCH /courses/{id}/chapters/reorder` | instructor | 07 |
| 26 | `POST /chapters/{id}/lessons` | instructor | 07 |
| 27 | `PATCH /lessons/{id}` | instructor | 07, 08 |
| 28 | `DELETE /lessons/{id}` | instructor | 07 |
| 29 | `PATCH /chapters/{id}/lessons/reorder` | instructor | 07 |
| 30 | `GET /lessons/{id}` | instructor, ta, student, parent | 08, 20 |
| 31 | `GET /lessons/{id}/materials` | instructor, ta, student, parent | 08, 20 |
| 32 | `POST /lessons/{id}/materials` | instructor | 08 |
| 33 | `DELETE /materials/{id}` | instructor | 08 |
| 34 | `GET /materials/{id}/download` | instructor, ta, student, parent | 20 |
| 35 | `POST /materials/{id}/view` | student | 20 |
| 36 | `GET /lessons/{id}/recordings` | instructor, ta, student, parent | 08, 20 |
| 37 | `POST /lessons/{id}/recordings` | instructor | 08 |
| 38 | `PATCH /recordings/{id}` | instructor | 08 |
| 39 | `DELETE /recordings/{id}` | instructor | 08 |
| 40 | `POST /recordings/{id}/watch` | student | 20 |
| 41 | `GET /lessons/{id}/assessments` | instructor, ta, student, parent | 08, 19 |
| 42 | `POST /lessons/{id}/assessments` | instructor | 08 |
| 43 | `PATCH /assessments/{id}` | instructor | 08 |
| 44 | `DELETE /assessments/{id}` | instructor | 08 |
| 45 | `POST /assessments/{id}/questions` | instructor | 08 |
| 46 | `PATCH /questions/{id}` | instructor | 08 |
| 47 | `DELETE /questions/{id}` | instructor | 08 |
| 48 | `PATCH /assessments/{id}/questions/reorder` | instructor | 08 |
| 49 | `POST /assessments/{id}/solutions` | instructor, ta | 15 |
| 50 | `GET /assessments/{id}` | student | 22, 23 |
| 51 | `POST /assessments/{id}/submissions` | student | 22, 23 |
| 52 | `PATCH /submissions/{id}/answers` | student | 22, 23 |
| 53 | `POST /submissions/{id}/submit` | student | 22, 23 |
| 54 | `GET /submissions/{id}` | student, instructor, ta, parent | 22, 23 |
| 55 | `GET /grading/queue` | instructor, ta | 06, 15 |
| 56 | `PATCH /submissions/{id}/answers/{answer_id}/grade` | instructor, ta | 15 |
| 57 | `POST /submissions/{id}/finalize` | instructor, ta | 15 |
| 58 | `GET /courses/{id}/groups` | instructor | 07, 09 |
| 59 | `POST /courses/{id}/groups` | instructor | 07, 09 |
| 60 | `PATCH /groups/{id}` | instructor | 09, 11 |
| 61 | `DELETE /groups/{id}` | instructor | 09 |
| 62 | `POST /groups/{id}/students` | instructor | 05, 11 |
| 63 | `DELETE /groups/{id}/students/{student_id}` | instructor | 11 |
| 64 | `GET /schedule` | instructor, ta, student, parent | 09, 14, 19, 17 |
| 65 | `POST /live-sessions` | instructor | 09 |
| 66 | `GET /live-sessions/{id}` | instructor, ta, student | 10, 21 |
| 67 | `PATCH /live-sessions/{id}` | instructor | 09 |
| 68 | `DELETE /live-sessions/{id}` | instructor | 09 |
| 69 | `POST /live-sessions/{id}/join` | student | 21 |
| 70 | `GET /live-sessions/{id}/attendance` | instructor, ta | 10, 16 |
| 71 | `PUT /live-sessions/{id}/attendance` | instructor, ta | 10, 16 |
| 72 | `POST /live-sessions/{id}/end` | instructor, ta | 10 |
| 73 | `GET /courses/{id}/roster` | instructor, ta | 11 |
| 74 | `GET /students/{id}` | instructor, ta, parent | 11, 18 |
| 75 | `POST /students` | instructor | 05 |
| 76 | `POST /students/{id}/parents/invite` | instructor | 05 |
| 77 | `GET /fees/summary` | instructor | 12 |
| 78 | `GET /fees/invoices` | instructor | 12 |
| 79 | `POST /fees/invoices` | instructor | 12 |
| 80 | `PATCH /fees/invoices/{id}` | instructor | 12 |
| 81 | `POST /fees/invoices/{id}/remind` | instructor | 12 |
| 82 | `GET /fees/invoices/{id}/receipt` | instructor, parent | 12, 18 |
| 83 | `GET /team/tas` | instructor | 13 |
| 84 | `POST /team/tas/invite` | instructor | 13 |
| 85 | `PATCH /team/tas/{user_id}` | instructor | 13 |
| 86 | `DELETE /team/tas/{user_id}` | instructor | 13 |
| 87 | `GET /ta/dashboard` | ta | 14 |
| 88 | `GET /parents/me/children` | parent | 17 |
| 89 | `GET /parents/me/children/{student_id}/attendance` | parent | 18 |
| 90 | `GET /parents/me/children/{student_id}/grades` | parent | 18 |
| 91 | `GET /parents/me/children/{student_id}/fees` | parent | 18 |
| 92 | `GET /parents/me/children/{student_id}/schedule` | parent | 18 |
| 93 | `GET /student/dashboard` | student | 19 |

---

## 6. Detailed endpoints

### 6.1 Authentication & onboarding — screens 01–05

#### `POST /auth/login`
**Access:** public
```json
// request
{ "email": "ahmed@example.com", "password": "••••••••" }
```
```json
// 200
{
  "access_token": "…", "refresh_token": "…",
  "user": { "id": "…", "first_name": "Ahmed", "role": "instructor" }
}
```
- `role` on the response is what the client uses for **[01] note 1**'s routing: `instructor→06`, `ta→14`, `parent→17`, `student→19`.
- Resolved from `USER_ROLES`; if (future) a user somehow has >1 role, the API returns the primary one and a `roles: []` array — client picks, defaulting to primary.
- `401 INVALID_CREDENTIALS` on mismatch — same generic message whether the email doesn't exist or the password is wrong (no user enumeration).

#### `POST /auth/refresh`
**Access:** public, requires valid refresh token
```json
{ "refresh_token": "…" }
```
Validates against `USER_SESSIONS` (`is_revoked = false`, `expires_at > now`), rotates the token (issues + stores a new hash, revokes the old one), returns a new `access_token`/`refresh_token` pair. `401 SESSION_REVOKED` or `401 SESSION_EXPIRED` if invalid.

#### `POST /auth/logout`
**Access:** any authenticated role. Sets `USER_SESSIONS.is_revoked = true` for the current session (from the refresh token or session id passed).

#### `POST /auth/forgot-password` — **[03]**
```json
{ "email": "…" }
```
Always `200 { "message": "If that email exists, a reset link has been sent." }` regardless of whether the account exists (**[03] note 1**). Creates a time-boxed reset token internally.

#### `POST /auth/reset-password` — **[03]**
```json
{ "token": "…", "new_password": "…" }
```
`410 TOKEN_EXPIRED` if the window has passed (**[03] note 2** — client should offer "resend").

#### `POST /auth/signup/instructor` — **[02] step 1**
```json
{
  "full_name": "Ahmed Hassan",
  "email": "ahmed@example.com",
  "password": "…",
  "subjects_taught": ["Physics"],
  "curriculum": "igcse"            // igcse | american_diploma | both
}
```
Creates `USERS` (role `instructor`) + `TEACHERS` row. Returns tokens immediately (account is usable, but flagged `billing_status: "pending"` until steps 2–3 complete) plus a `next_step` hint — the client uses this to keep the stepper on step 2, not to gate login.

#### `POST /instructor/subscription` — **[02] step 2**
**Access:** instructor
```json
{ "plan_id": "…" }
```
Creates a `SUBSCRIPTIONS` row with `status = pending`. Plan tiers are keyed off student-count/TA-seat limits as shown in `SUBSCRIPTION_PLANS`.

#### `POST /subscriptions/{id}/checkout` — **[02] step 3**
**Access:** instructor. Hands off to the payment provider (Stripe/Paymob-style — provider TBD, out of scope for this doc); on provider webhook confirmation the API flips `SUBSCRIPTIONS.status = active`. Response includes a `checkout_url` for the client to redirect to.
- On success, client is routed straight into `POST /courses` → Curriculum Builder (**[02] note 2** — avoids empty-dashboard drop-off), not the dashboard.

#### `GET /invites/{token}` — **[04], [05]**
**Access:** public. Resolves an invite token to show context before the user sets a password:
```json
{
  "invite_type": "ta",                 // ta | student | parent
  "inviter_name": "Mr. Ahmed",
  "scope_preview": "attendance, grading, and homework uploads for his classes",
  "email": "…", "expires_at": "…"
}
```
`404 INVITE_NOT_FOUND` / `410 INVITE_EXPIRED`.

#### `POST /invites/{token}/accept` — **[04], [05]**
**Access:** public
```json
{ "full_name": "Nour F.", "password": "…" }   // full_name only required for TA invites; student/parent names are pre-set by the instructor at invite time
```
- TA invite → creates `USERS` (role `ta`) if not already existing, activates the `GROUP_ASSISTANTS` row(s) created at invite time, returns tokens. Client routes to **[14]**.
- Student invite → activates the `STUDENTS` row created by `POST /students`, returns tokens, routes to **[19]**.
- Parent invite → activates the `USERS`/`PARENT_STUDENTS` row created by `POST /students/{id}/parents/invite`, returns tokens, routes to **[17]**.

---

### 6.2 Profile & notifications (cross-cutting)

#### `GET /me`
Returns the caller's `USERS` row plus role-specific profile (`TEACHERS` or `STUDENTS` sub-object) and resolved `role`.

#### `PATCH /me` — **[13] Profile tab**
Updates editable profile fields (`first_name`, `last_name`, `bio`, `specialization` for instructors, etc).

#### `GET /notifications`
**Access:** any. Powers **[17]**'s "Recent updates" feed and **[06]**'s badges, and is the polling fallback for anything described as real-time (§3.6).
```
?unread_only=true&page=1&limit=20
```

#### `PATCH /notifications/{id}/read`
Marks one notification read. (Bulk: `PATCH /notifications/read-all`.)

---

### 6.3 Instructor Dashboard — screen 06

#### `GET /instructor/dashboard`
**Access:** instructor. One call to hydrate the whole screen (avoids 6 separate round-trips for a page that's mostly summary stats):
```json
{
  "stats": { "total_students": 158, "active_courses": 6, "sessions_this_week": 4, "pending_grading": 12 },
  "todays_sessions": [ { "live_session_id": "…", "time": "10:00", "class_name": "IG Physics — Section B",
                          "mode": "online", "join_url": "…" } ],
  "needs_grading": [ { "assessment_id": "…", "title": "Quiz — Kinematics", "pending_count": 24 } ]
}
```
- The four stat cards deep-link to `GET /courses` (or `?filter=`), `GET /students`, `GET /schedule` — pre-filtered client-side, per **[06] note 3**.
- "Needs grading" is the same data as `GET /grading/queue` grouped by assessment; "Go to Grading" is that endpoint.

---

### 6.4 Courses & Curriculum Builder — screen 07 (+ role-aware navigation into 08 / 20)

> **This is the section that answers your navigation question directly.** The *same two endpoints* (`GET /courses` and `GET /courses/{id}/curriculum`) serve both the instructor's Curriculum Builder and the student's read-only course view. The response shape and content differ by resolved role — the client doesn't need separate "instructor course list" vs "student course list" endpoints, and it doesn't need to decide client-side whether to render the builder or the viewer; the API tells it.

#### `GET /courses` — **[06]→07, 19]**
**Access:** instructor, student
- **As instructor:** returns courses where `COURSES.teacher_id = current_user`.
- **As student:** returns courses reachable via `STUDENT_GROUPS → GROUPS → COURSES` for the current student — i.e. every course the student is enrolled in through any group.
- (TAs don't call this — their portal has no "Courses" nav item, per **[14] note 1**; a TA's assigned courses surface only via `GET /ta/dashboard` and `GET /grading/queue`.)

```json
{
  "data": [
    { "course_id": "…", "course_name": "IG Physics", "course_code": "…",
      "grade_level": "Grade 10", "curriculum": "igcse", "status": "published",
      "viewer_role": "instructor" }
  ]
}
```
`viewer_role` on each item tells the client which screen to open on click: `instructor` (or `ta`) → Curriculum Builder (**07**) / Content Hub (**08**); `student` → Lesson & Materials View (**20**).

#### `POST /courses` — **[07]**
**Access:** instructor
```json
{ "course_code": "PHYS-101", "course_name": "IG Physics", "description": "…",
  "grade_level": "Grade 10", "curriculum": "igcse", "fees": 1500.00 }
```
`status` defaults to `draft`.

#### `GET /courses/{id}` — **[07], [20]**
**Access:** instructor (owner), ta (assigned to a group under this course), student (enrolled), parent (child enrolled)
Returns course metadata plus `viewer_role` and `can_edit: boolean` — the latter is `true` only for the owning instructor (never true for TAs; curriculum editing is instructor-only per the wireframe, TAs get grading/attendance only).
`403 FORBIDDEN` if the caller has no relationship to the course (not owner, not enrolled, not assigned).

#### `PATCH /courses/{id}` / `DELETE /courses/{id}` — **[07]**
**Access:** instructor (owner only). `DELETE` is soft (sets `status = archived`) if any `GROUPS`/`STUDENT_GROUPS` exist under it, to avoid orphaning enrollment/grade history — hard delete only allowed on an empty course.

#### `GET /courses/{id}/curriculum` — **[07], [08]→20]**
**Access:** instructor, ta, student, parent
The chapter → lesson tree, **filtered by role**:
- **Instructor / assigned TA:** full tree, every chapter/lesson regardless of `status`, each lesson annotated `editable: true`.
- **Student / parent:** only chapters that contain at least one `status = published` lesson; draft lessons are **omitted from the response entirely**, not just hidden client-side (**[07] note 3** — "drafts are invisible to students"). This is also why parents can't accidentally see unpublished content through a shared component.

```json
{
  "course_id": "…", "viewer_role": "student",
  "chapters": [
    { "chapter_id": "…", "chapter_title": "Chapter 1 — Kinematics", "order_index": 1,
      "lessons": [
        { "lesson_id": "…", "title": "1.1 Distance & Displacement", "order_index": 1, "status": "published" }
      ] }
  ]
}
```

#### `POST /courses/{id}/chapters` — **[07]**
**Access:** instructor
```json
{ "chapter_title": "Chapter 2 — Forces", "description": "…" }
```
`order_index` auto-assigned to end of list unless `position` passed.

#### `PATCH /chapters/{id}` / `DELETE /chapters/{id}` — **[07]**
**Access:** instructor. `DELETE` cascades to lessons only if empty of published lessons with submissions — otherwise `409 CHAPTER_NOT_EMPTY` (protects grade history).

#### `PATCH /courses/{id}/chapters/reorder` — **[07] note 1 (drag-to-reorder)**
```json
{ "ordered_chapter_ids": ["…", "…", "…"] }
```

#### `POST /chapters/{id}/lessons` — **[07]**
```json
{ "title": "1.3 Acceleration", "description": "…" }
```
`status` defaults to `draft`.

#### `PATCH /lessons/{id}` — **[07], [08]**
```json
{ "title": "…", "description": "…", "status": "published" }
```
Flipping `status` to `published` is what makes it appear in student `GET /courses/{id}/curriculum` responses and triggers `NOTIFICATIONS`/socket event `lesson.published` (**[08] note 3**).

#### `DELETE /lessons/{id}` / `PATCH /chapters/{id}/lessons/reorder` — **[07]**
Same drag-reorder pattern as chapters.

#### `GET /lessons/{id}` — **[08], [20]**
**Access:** instructor, ta, student, parent. Lesson detail — the anchor resource that Materials/Recordings/Assessments all hang off of. Role-filtered the same way as the curriculum tree (a draft lesson `404`s for a student, not just `403`s, to avoid confirming it exists).

---

### 6.5 Content & Assessment Hub — screen 08 (Materials / Quiz Builder / Homework tabs)

#### `GET /lessons/{id}/materials` — **[08], [20]**
**Access:** instructor, ta, student, parent (role-filtered as above)
```json
{ "data": [
  { "material_id": "…", "title": "Lecture Notes — Speed & Velocity.pdf", "file_url": "…",
    "size_bytes": 1258291, "access_mode": "downloadable", "uploaded_at": "…" }
] }
```
`access_mode` (`view_only` | `downloadable`) is set at upload time per **[08] note 1**.

#### `POST /lessons/{id}/materials` — **[08]**
**Access:** instructor. `multipart/form-data`: `file`, `title`, `access_mode`.

#### `DELETE /materials/{id}` — **[08]**
**Access:** instructor

#### `GET /materials/{id}/download` — **[20]**
**Access:** instructor, ta, student, parent (enrolled/assigned only). Returns a short-lived signed URL; for `access_mode = view_only` the URL is a streaming/preview link rather than an attachment-disposition download.

#### `POST /materials/{id}/view` — **[20] note 2**
**Access:** student. Logs a "viewed" event visible to the instructor on the Roster (**11**) as an engagement signal beyond attendance. No body needed; `201` with `{ "viewed_at": "…" }`.

#### `GET /lessons/{id}/recordings` / `POST /lessons/{id}/recordings` / `PATCH /recordings/{id}` / `DELETE /recordings/{id}` — **[08]**
Standard CRUD over `RECORDED_SESSIONS`. `POST` body:
```json
{ "title": "Recorded lecture", "video_url": "…", "duration_seconds": 2520,
  "max_watch_limit": 3, "publish_at": "…", "deadline": "…",
  "recorded_from_live_session_id": null }   // set when auto-created from an ended live session, see 6.6
```

#### `POST /recordings/{id}/watch` — **[20]**
**Access:** student. Increments a per-student watch counter (not in the base ERD as a separate table — implemented as a row in a lightweight watch-log keyed by `(recorded_session_id, student_id)`, count checked against `max_watch_limit`). `403 WATCH_LIMIT_REACHED` once exhausted.

#### `GET /lessons/{id}/assessments?type=quiz|homework` — **[08], [19]**
**Access:** instructor, ta, student, parent. List of `ASSESSMENTS` for the lesson, filtered by `type`.

#### `POST /lessons/{id}/assessments` — **[08] Quiz Builder / Homework tab**
**Access:** instructor
```json
{ "title": "Quiz — Kinematics", "type": "quiz", "group_id": "…", "max_score": 20, "due_date": "…" }
```
For a homework assignment, `type: "homework"` — the client then calls `POST /assessments/{id}/questions` once with `question_type: "file_upload"` to create the single submission slot (§3.4), rather than a bespoke homework endpoint.

#### `PATCH /assessments/{id}` / `DELETE /assessments/{id}` — **[08]**
**Access:** instructor

#### `POST /assessments/{id}/questions` — **[08] "+ Add Question"**
**Access:** instructor
```json
{ "question_text": "Which quantity is a vector?", "question_type": "mcq",
  "options": [{ "id": "a", "text": "Speed" }, { "id": "b", "text": "Velocity" }],
  "model_answer": "b", "points": 2 }
```
`model_answer` is **never** included in any response a student can see (`GET /assessments/{id}` below strips it).

#### `PATCH /questions/{id}` / `DELETE /questions/{id}` / `PATCH /assessments/{id}/questions/reorder` — **[08]**
**Access:** instructor

#### `POST /assessments/{id}/solutions` — **[15] "+ Upload homework solutions"**
**Access:** instructor, ta (if `homework_upload` in their `GROUP_ASSISTANTS.permissions`, §3.3). `multipart/form-data` — stored as a `MATERIALS` row with `assessment_id` set (§3.5), released to students only once `ASSESSMENT_SUBMISSIONS.status = graded` for them individually.

---

### 6.6 Scheduling & Live Sessions — screens 09, 10, 21

#### `GET /schedule?start=&end=&view=week|month` — **[09], [14], [19], [17]**
**Access:** instructor, ta, student, parent — each scoped to their own reachable sessions (owned courses / assigned groups / enrolled groups / linked children's groups respectively). One unified calendar endpoint for both online and offline sessions, per **[09]**'s "one calendar" framing.

#### `POST /live-sessions` — **[09] "+ New Session"**
**Access:** instructor
```json
{
  "group_id": "…", "lesson_id": "…", "title": "IG Physics B",
  "mode": "online", "meeting_url": null,      // null + mode=online → auto-generate if a video provider is connected
  "scheduled_start": "…", "scheduled_end": "…",
  "recurrence": { "frequency": "weekly", "until": "…" }   // omit for one-off
}
```
For `mode: "offline"`, `classroom_location` replaces `meeting_url`.

#### `PATCH /live-sessions/{id}?scope=this_only|this_and_following` — **[09] note 3**
**Access:** instructor. `scope` is required whenever the session belongs to a recurring series; editing prompts the "this session only / this and following" choice shown in the wireframe.

#### `DELETE /live-sessions/{id}?scope=this_only|this_and_following` — **[09]**

- Any create/update/delete here fires `session.updated`/`session.cancelled` (§8) and a `NOTIFICATIONS` row for enrolled students + their linked parents (**[09] note 2**).

#### `GET /live-sessions/{id}` — **[10], [21]**
**Access:** instructor, ta (assigned), student (enrolled). Includes `meeting_url` (or `classroom_location`), current `status`, and (for instructor/ta) the live attendance roster.

#### `POST /live-sessions/{id}/join` — **[21]**
**Access:** student. Returns the embed/meeting URL. If within the join window, also writes an `ATTENDANCE` row (`status: present`, `recorded_at: now`) — this is the "auto-captured on join" behavior in **[21] note 2**. Leaving before a minimum duration threshold (config) can later be reconciled to `late`/`excused` by the instructor via `PUT /live-sessions/{id}/attendance`.

#### `GET /live-sessions/{id}/attendance` — **[10], [16]**
**Access:** instructor, ta (if `attendance` in their `permissions`)

#### `PUT /live-sessions/{id}/attendance` — **[10], [16]**
**Access:** instructor, ta (scoped as above). Bulk upsert — same shape whether it's the instructor's Session View (**10**, with video) or the TA's plain Attendance Taking screen (**16**), per **[16] note 1**.
```json
{ "records": [ { "student_id": "…", "status": "present" }, { "student_id": "…", "status": "absent" } ] }
```
`{ "records": [{ "student_id": "*", "status": "present" }] }` is accepted as shorthand for "Mark all present".

#### `POST /live-sessions/{id}/end` — **[10] "End Session & Save Attendance"**
**Access:** instructor, ta. Sets `LIVE_SESSIONS.status = completed`, persists final attendance, and fires the real-time update that flips the parent's attendance badge (**[10] note 3**, **[16] note 2**). Optionally accepts `create_recording: { video_url, duration_seconds }` to immediately spin up a `RECORDED_SESSIONS` row with `recorded_from_live_session_id` set — covers the "may be recorded as" ERD relationship.

---

### 6.7 Student Roster & Performance — screen 11

#### `GET /courses/{id}/roster?group_id=&status=missing_homework|low_attendance&search=` — **[11]**
**Access:** instructor, ta (scoped to assigned groups)
```json
{ "data": [
  { "student_id": "…", "name": "Mariam K.", "section": "B",
    "attendance_pct": 96, "last_quiz_pct": 88, "homework_status": "submitted" }
] }
```
`status` filters implement the "missing homework" / "low attendance" triage from **[11] note 2**; `low_attendance` is a server-side threshold param, not a fixed constant, so it can be tuned per instructor later.

#### `GET /students/{id}` — **[11] row click, 18]**
**Access:** instructor, ta (scoped), parent (own children only)
Full detail panel: attendance history, quiz/homework record, linked parent contact — **[11] note 1**'s "single source of truth" replacing the WhatsApp-with-parents workflow.
```json
{
  "student_id": "…", "name": "Mariam K.", "student_code": "…", "grade_level": "…",
  "parents": [ { "name": "…", "phone": "…", "email": "…" } ],
  "attendance": { "pct": 96, "history": [ /* … */ ] },
  "assessments": [ /* … */ ]
}
```

---

### 6.8 Fees & Revenue — screen 12

#### `GET /fees/summary` — **[12]**
**Access:** instructor
```json
{ "this_month_revenue": 42500.00, "outstanding": 3200.00, "paid_on_time_pct": 91 }
```

#### `GET /fees/invoices?group_id=&status=` — **[12]**
**Access:** instructor. Backs the fees table (student, section, plan, status).

#### `POST /fees/invoices` — **[12]**
**Access:** instructor. Generates an invoice for a student/course/period, defaulting `amount` to `COURSES.fees`.

#### `PATCH /fees/invoices/{id}` — **[12]**
**Access:** instructor. Used to mark `status: paid` manually (cash/bank transfer) or record `payment_method`. Updates propagate instantly to the parent's fee badge — same data feeds `GET /parents/me/children` and **[18]**'s Fees tab (**[12] note 2**).

#### `POST /fees/invoices/{id}/remind` — **[12] "Send reminder"**
**Access:** instructor. Fires a `fee_reminder` notification straight to the linked parent(s) via `PARENT_STUDENTS` (**[12] note 1**) — no manual chasing.

#### `GET /fees/invoices/{id}/receipt` — **[12] "Receipt" link, 18]**
**Access:** instructor, parent (own child's invoice only). Returns a receipt PDF/URL.

---

### 6.9 Team / TA management — screen 13

#### `GET /team/tas` — **[13]**
**Access:** instructor. TAs with their scope (`all sections` or specific group names) and `permissions`.

#### `POST /team/tas/invite` — **[13] "+ Invite TA"**
**Access:** instructor
```json
{ "email": "…", "full_name": "…", "group_ids": ["…"], "permissions": ["attendance", "grading"] }
```
Creates the `GROUP_ASSISTANTS` row(s) (pending, activated on invite acceptance) and sends the invite email consumed by `GET /invites/{token}` (**04**).

#### `PATCH /team/tas/{user_id}` — **[13] "Edit"**
**Access:** instructor. Updates `group_ids` and/or `permissions`.

#### `DELETE /team/tas/{user_id}` — **[13] "Revoke"**
**Access:** instructor. Removes `GROUP_ASSISTANTS` rows (access revoked immediately) but **does not** delete or anonymize any grading the TA already did — `ASSESSMENT_SUBMISSIONS.graded_by_user_id` stays intact for audit history (**[13] note 2**).

---

### 6.10 TA Portal — screens 14, 15, 16

#### `GET /ta/dashboard` — **[14]**
**Access:** ta
```json
{
  "assigned_sections": ["IG Physics — A", "IG Physics — B", "IG Physics — Revision"],
  "pending_grading_count": 24,
  "todays_sessions": [ { "live_session_id": "…", "time": "16:00", "class_name": "IG Physics Revision" } ]
}
```
Everything here is pre-scoped server-side to the TA's `GROUP_ASSISTANTS` rows — there is no client-side filtering, and the TA's JWT scope means `GET /courses`, `GET /fees/*`, `GET /team/*` all `403` for this role regardless of UI (**[14] note 2** — instructor-only areas are enforced, not just hidden).

#### `GET /grading/queue?assessment_id=` — **[15]**
**Access:** instructor, ta (scoped, requires `grading` permission for TAs)
Returns only **ungraded structured/file-upload answers** — MCQ answers are excluded because they're already auto-graded on submit (**[15] note 1**).
```json
{ "data": [
  { "answer_id": "…", "submission_id": "…", "student_name": "Youssef T.",
    "question_text": "Q4 (structured answer)", "points_possible": 2, "student_answer": "…", "file_url": null }
] }
```

#### `PATCH /submissions/{id}/answers/{answer_id}/grade` — **[15]**
**Access:** instructor, ta (scoped)
```json
{ "points_awarded": 1.5, "evaluator_comment": "Correct direction, missing units." }
```

#### `POST /submissions/{id}/finalize` — **[15]**
**Access:** instructor, ta. Sums `points_awarded` across all answers (MCQ auto-graded + just-graded structured ones) into `ASSESSMENT_SUBMISSIONS.total_score`, sets `status: graded`, `graded_by_user_id`, `graded_at`. This is what syncs to the student's result and the parent's Child Detail view in real time (**[15] note 2**).

#### `GET /live-sessions/{id}/attendance` / `PUT /live-sessions/{id}/attendance` — **[16]**
Same endpoints as **10** (§6.6) — Attendance Taking is the identical component, scoped to whichever session the TA is assigned to cover.

---

### 6.11 Parent Portal — screens 17, 18

#### `GET /parents/me/children` — **[17]**
**Access:** parent. One call for the whole home screen — cards + recent updates.
```json
{
  "children": [
    { "student_id": "…", "name": "Youssef", "course_name": "IG Physics",
      "attendance_pct": 70, "avg_grade_pct": 54 },
    { "student_id": "…", "name": "Layla", "course_name": "American Diploma Math",
      "attendance_pct": 45, "fee_status": "overdue" }
  ],
  "recent_updates": [
    { "type": "attendance_alert", "message": "Layla missed today's 4:00 PM session", "created_at": "…" },
    { "type": "grade_posted", "message": "Youssef scored 54% on Kinematics quiz", "created_at": "…" }
  ]
}
```
Resolved via `PARENT_STUDENTS.parent_id = current_user` (§3.1) — this is what makes "one parent, multiple children/instructors" (**[17] note 2**) work; there's no per-child login.

#### `GET /parents/me/children/{student_id}/attendance` — **[18] Attendance tab**
`GET /parents/me/children/{student_id}/grades` — **[18] Grades tab**
`GET /parents/me/children/{student_id}/fees` — **[18] Fees tab**
`GET /parents/me/children/{student_id}/schedule` — **[18] Schedule tab**

**Access:** parent, and only if `PARENT_STUDENTS` links them to `student_id` — `403` otherwise. All four are **read-only**; there is intentionally no `PATCH`/`POST` here (**[18] note 1** — parents monitor, never edit). The Fees tab's data is identical to `GET /fees/invoices?student_id=` filtered instructor-side, and paying (via `GET /fees/invoices/{id}/receipt`'s linked checkout, or a future `POST /fees/invoices/{id}/pay`) clears the badge in real time on `GET /parents/me/children` (**[18] note 2**).

---

### 6.12 Student Portal — screens 19–23

#### `GET /student/dashboard` — **[19]**
**Access:** student
```json
{
  "next_up": { "live_session_id": "…", "title": "IG Physics — Live Class", "starts_at": "…", "joinable": true },
  "due_soon": [ { "assessment_id": "…", "title": "Quiz — Kinematics", "due_date": "…" } ],
  "recent_grades": [ { "assessment_id": "…", "title": "Homework 1.1", "score": "8/10" } ]
}
```
- `joinable` is `true` only inside the session's join window (**[19] note 1**) — otherwise the client renders a countdown from `starts_at`.
- `due_soon` aggregates `ASSESSMENTS` across every enrolled course sorted by `due_date` (**[19] note 2**).

#### `GET /lessons/{id}` + `GET /lessons/{id}/materials` + `GET /lessons/{id}/recordings` — **[20]**
Same endpoints as §6.5, called from the student's Lesson & Materials view. Published-only, as covered in §6.4.

#### `GET /live-sessions/{id}` + `POST /live-sessions/{id}/join` — **[21]**
Same endpoints as §6.6.

#### `GET /assessments/{id}` — **[22]** (quiz) / **[23]** (homework)
**Access:** student (enrolled in the assessment's group)
Returns questions **without** `model_answer`, plus a `time_remaining_seconds` if the assessment is timed.

#### `POST /assessments/{id}/submissions` — **[22], [23]**
**Access:** student. Creates (or resumes, if one is already `in_progress`) an `ASSESSMENT_SUBMISSIONS` row.

#### `PATCH /submissions/{id}/answers` — **[22], [23]**
**Access:** student (own submission only)
```json
{ "answers": [ { "question_id": "…", "student_answer": "b" } ] }
```
For homework, the single `file_upload` question's answer is a `file_url` from a prior upload call rather than `student_answer` text. Called on every question navigation for autosave — this backs the "jump between answered/unanswered questions" navigator in **[22] note 1**.

#### `POST /submissions/{id}/submit` — **[22], [23]**
**Access:** student.
- MCQ-only assessments: auto-grades immediately, `status → graded`, score returned in the response (**[22] note 2**).
- Any structured/file-upload questions present: MCQ portion scores immediately but overall `status → submitted` (pending human grading) until an instructor/TA finalizes it via `POST /submissions/{id}/finalize`.
- Homework specifically: submissions after `ASSESSMENTS.due_date` are accepted but flagged `late: true` on the submission, visible to instructor (**11**) and parent (**18**), never silently hidden (**[23] note 1**). Re-submission (calling this endpoint again) is allowed while `status != graded` — grading locks it (**[23] note 2**), enforced as `409 SUBMISSION_LOCKED` on further submit attempts once graded.

#### `GET /submissions/{id}` — **[22], [23]**
**Access:** student (own), instructor/ta (scoped), parent (own child's). Result view — scores, per-question feedback once graded.

---

## 7. Enrollment (screen 05, feeding into 07/11)

#### `POST /students` — **[05]**
**Access:** instructor
```json
{ "first_name": "…", "last_name": "…", "school_name": "…", "grade_level": "…",
  "parent_phone": "…", "parent_email": "…", "group_id": "…" }
```
Creates the `USERS`/`STUDENTS` rows (pending activation) and, if `group_id` given, the `STUDENT_GROUPS` row; sends the student invite consumed by `GET /invites/{token}` (**04**/**05**). If `parent_email` is present, also calls the equivalent of §7's parent-invite step in the same transaction — matching **[05] note 1** ("instructor can invite the parent and student together").

#### `POST /students/{id}/parents/invite` — **[05]**
**Access:** instructor (or student, self-service — **[05] note 1**, "student can add a parent later from their own settings")
```json
{ "email": "…", "phone": "…" }
```
Creates/reuses a `USERS` row (role `parent`) and a `PARENT_STUDENTS` link, auto-approved (no manual matching step) — sends the parent invite (**05**).

#### `POST /groups/{id}/students` — **[11]**
**Access:** instructor. Enrolls an *existing* student into an additional group (vs. `POST /students` which creates a new student + enrolls in one call).

#### `DELETE /groups/{id}/students/{student_id}` — **[11]**
**Access:** instructor. Removes the `STUDENT_GROUPS` link (doesn't delete the student or their history).

---

## 8. Real-time events (optional layer, §3.6)

```
WSS /ws?token=<access_token>
```
Server-pushed events, each mirroring a write above and always also landing in `NOTIFICATIONS`:

| Event | Fired by | Consumed by |
|---|---|---|
| `session.scheduled` / `session.updated` / `session.cancelled` | 09 | student, parent (schedule) |
| `attendance.updated` | 10, 16 | parent (badge) |
| `lesson.published` | 07/08 | student (curriculum) |
| `grade.posted` (submission finalized) | 15 | student, parent |
| `fee.updated` (invoice paid/overdue) | 12 | parent (badge) |
| `invite.accepted` | 04/05 accept | instructor |

A client that never opens the socket still gets everything via `GET /notifications` — the socket is a latency optimization, not a dependency.

---

## 9. Error codes

| HTTP | Code | Meaning |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Malformed/missing fields — `details` lists per-field errors |
| 401 | `INVALID_CREDENTIALS` | Login failed |
| 401 | `SESSION_EXPIRED` / `SESSION_REVOKED` | Refresh token invalid |
| 403 | `FORBIDDEN` | Authenticated but not permitted for this resource |
| 404 | `RESOURCE_NOT_FOUND` | Also returned instead of 403 where existence itself shouldn't be confirmed (e.g. a draft lesson to a student) |
| 409 | `CHAPTER_NOT_EMPTY` / `SUBMISSION_LOCKED` / `WATCH_LIMIT_REACHED` | State conflict — see relevant endpoint |
| 410 | `TOKEN_EXPIRED` / `INVITE_EXPIRED` | Time-boxed token past expiry |
| 422 | `UNPROCESSABLE_ENTITY` | Well-formed but semantically invalid (e.g. `scheduled_end` before `scheduled_start`) |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unhandled server error |

---

## 10. Open items to confirm with you

1. **§3.1** `PARENT_STUDENTS` — OK to add this join table? It's the only way to represent "one parent, many children" from screen 17.
2. **§3.2** `INVOICES` — OK to add this table for student course-fee tracking? Or is there an existing billing/payments system this should integrate with instead of owning the data itself?
3. **§3.3** TA `permissions` — OK to extend `GROUP_ASSISTANTS` with a `permissions` array, or would you rather this be a fixed set of TA "levels" (e.g. `full` vs `attendance_only`) instead of an arbitrary combination?
4. **Payment provider** for §6.1's checkout and §6.8's parent-side "pay now" — not specified in the wireframes; I left it as a placeholder integration point.
5. **Recording storage/transcoding** — `video_url` is treated as already-hosted media; if you need the API to own upload/transcoding (vs. just storing a URL from an external service), that's a separate set of endpoints not included here.
6. **§3.6** Where should "create a group/section" live in the UI? No wireframe screen shows it, but it has to happen before students, TAs, or sessions can be attached to a course.
