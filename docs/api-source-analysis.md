# API Design — Source Analysis & Key Notes

Working notes distilled from the three sources of truth, to be used as the shared context for the API documentation effort. Every claim below is referenced back to its source.

**Sources**
| Ref key | File | What it authoritatively defines |
|---|---|---|
| `SCOPE` | `docs/Montu - E-Learning Platform.md` | Product vision, roles, feature pillars, personas |
| `ERD` | `docs/erd.md` | Entities, fields, relationships, constraints, delete rules |
| `WF` | `docs/elearning-platform-wireframes.html` | 24 screens (`s-*` ids), interactions, edge cases, cross-screen sync rules |
| `CODE` | `prisma/schema.prisma`, `src/` | Current implementation state (scaffolding only) |

---

## 1. Product in one paragraph

A centralized LMS for independent IGCSE / American-Diploma instructors, replacing WhatsApp + Drive + Zoom + external quiz tools. Four linked account tiers — **Instructor** (root account), **Teaching Assistant** (delegated), **Parent** (read-only monitor), **Student** — all reading from one curriculum, one schedule, one gradebook, with real-time propagation between tiers. `SCOPE §1–§3`, `WF #s-overview`.

**Two personas drive non-functional priorities:**
- *Mr. Ahmed* — 150+ students, multi-section: needs **bulk/fast** writes (post quiz, schedule session in seconds), **cross-section aggregate reads**, triage filters. `SCOPE §4 P1`, `WF #s-idash`, `#s-roster`.
- *Parent Sara* — needs **push-fresh, mobile-light, read-only** views; attendance/grade visible the moment a session ends or a quiz is graded. `SCOPE §4 P2`, `WF #s-phome`.

---

## 2. Domain model — the two branches (most important structural fact)

`ERD:1-12` splits what used to be one `SESSIONS` table into two independent branches. **All API resource paths must respect this split.**

```
CURRICULUM (cohort-independent, authored once)
  COURSES → CHAPTERS → LESSONS → { MATERIALS, RECORDED_SESSIONS, ASSIGNMENTS → SUBMISSIONS }

COHORTS (group-specific, per class instance)
  COURSES → GROUPS → { LIVE_SESSIONS → ATTENDANCE, QUIZZES → QUESTIONS/ATTEMPTS → ANSWERS }
```

- A `LIVE_SESSION` is one scheduled class (onsite or online) and is the **only** thing `ATTENDANCE` records against. `ERD:224-244`
- `LIVE_SESSIONS.lesson_id` is **nullable on purpose** — revision/exam-prep/Q&A classes map to no lesson. `ERD:497-529`, matches `WF #s-calendar` ("IG Physics Revision").
- `RECORDED_SESSIONS.recorded_from_live_session_id` is nullable + unique — at most one recording per live class; most recordings are pre-authored. `ERD:154-166`, `ERD:364-383`
- `GROUPS.schedule_info` / `classroom_location` are **defaults, not truth**; the authoritative time/place is on the `LIVE_SESSIONS` row. `ERD:497-529`

**Vocabulary mapping:** wireframes say "Section A / Section B / Revision" (`WF #s-roster`, `#s-tadash`); the ERD calls this a **GROUP**. Treat *section == group* throughout the API.

### Entity inventory (`ERD:19-296`)
| Cluster | Entities |
|---|---|
| Identity & access | `USERS`, `ROLES`, `USER_ROLES`, `USER_SESSIONS`, `TEACHERS`, `STUDENTS`, `PARENTS`, `PARENT_STUDENTS`, `INVITES`, `INVITE_GROUPS`, `NOTIFICATIONS` (password-reset OTP in cache) |
| Billing (platform) | `SUBSCRIPTION_PLANS`, `SUBSCRIPTIONS` |
| Curriculum | `COURSES`, `CHAPTERS`, `LESSONS`, `RECORDED_SESSIONS`, `MATERIALS`, `ASSIGNMENTS` |
| Cohorts | `GROUPS`, `GROUP_ASSISTANTS`, `STUDENT_GROUPS`, `LIVE_SESSIONS`, `ATTENDANCE`, `QUIZZES` |
| Assignments (curriculum) | `ASSIGNMENTS`, `ASSIGNMENT_SUBMISSIONS` |
| Quizzes (cohort) | `QUIZZES`, `QUIZ_QUESTIONS`, `QUIZ_ATTEMPTS`, `QUIZ_ANSWERS` |

---

## 3. Rules the API layer must enforce (not expressible as FKs)

`ERD:398-407` — **service-layer invariants**, i.e. they belong in request validation and must be documented as `422`/`409` error cases:

1. `LIVE_SESSIONS.lesson_id`, when set → the lesson's `chapter.course_id` must equal the group's `course_id`.
2. `RECORDED_SESSIONS.recorded_from_live_session_id`, when set → source live session's `lesson_id` must match the recording's `lesson_id`.
3. `QUIZZES.lesson_id`, when set → same course check as (1). `ASSIGNMENTS` needs no check — it is natively on the curriculum branch.

`ERD:384-397` — CHECK constraints surfacing as validation errors:
- `mode=ONLINE ⇒ meeting_url required`; `mode=ONSITE ⇒ classroom_location required` (drives the `WF #s-calendar` "+ New Session" online/offline toggle).
- `scheduled_end > scheduled_start`; `SUBSCRIPTIONS.end_date > start_date`; `max_watch_limit >= 0` where **0 = unlimited**.

`ERD:465-496` — delete semantics that must be reflected in `DELETE` endpoint docs:
- Curriculum spine `CASCADE`s; `LESSONS → LIVE_SESSIONS.lesson_id` is `SET NULL` — **deleting a lesson must never destroy attendance history**.
- `GROUPS → LIVE_SESSIONS` is `RESTRICT` → **groups are archived, never deleted** once they have history. The API should expose archive, not delete, for cohorts.

`ERD:436-464` — existing indexes tell us the intended hot queries, which the endpoints should mirror:
`LIVE_SESSIONS (group_id, scheduled_start)` = the timetable query; `QUIZZES (group_id, closes_at)` = "due soon"; `NOTIFICATIONS (user_id, is_read)` = the parent/student feed.

---

## 4. Roles & access hierarchy

`ROLES` enum = `TEACHER, STUDENT, ASSISTANT, PARENT, ADMIN` (`ERD:31-34`); `USER_ROLES` is many-to-many, so a user may hold several roles and **login resolves role server-side and routes** — one login for all tiers. `WF #s-login`.

| Role | Can do | Cannot do | Ref |
|---|---|---|---|
| Instructor (TEACHER) | Everything under their own courses: curriculum, content, quizzes, schedule, attendance, grading, roster, fees, TA invites, billing | — | `SCOPE §3.A`, `WF #s-idash`, `#s-isettings` |
| TA (ASSISTANT) | Attendance, grading, homework-solution upload — **scoped to assigned groups, each behind its own permission flag** | Course building, scheduling, fees, settings | `WF #s-tadash`, `#s-tainvite`, `#s-grading`, `#s-attendance` |
| Parent | Read-only: attendance, grades, fees, schedule of linked children; pay fees | Never edits grades/attendance/schedule | `SCOPE §3.A`, `WF #s-pchild` ("All four tabs are read-only") |
| Student | View published lessons/materials/recordings, join live class, take quizzes, submit homework | Anything authoring | `SCOPE §3.A`, `WF #s-shome`–`#s-homework` |

Notable access rules:
- Only instructors can self-sign-up; **TA, parent and student accounts are always created by invite** — issued by an instructor, or by a student inviting their own parent (WF 05). `WF #s-login`, `#s-tainvite`, `#s-familyinvite`
- Revoking a TA removes access **without deleting their grading history**. `WF #s-isettings`
- One parent account links to **multiple children across multiple instructors**; parent switches children without re-login. `WF #s-login`, `#s-familyinvite`, `#s-phome`

---

## 5. Screen → data/endpoint map

| # | Screen (`id`) | Reads | Writes |
|---|---|---|---|
| 01 | Login `s-login` | — | session create (role-based routing) |
| 02 | Instructor sign-up `s-signup` | plans | user + TEACHER + subscription (3 steps: account → plan → payment) |
| 03 | Forgot password `s-forgot` | — | reset request (uniform response, no account-existence leak; emailed OTP, not a link) |
| 04 | TA invite `s-tainvite` | invite token + scope preview | activate account |
| 05 | Parent/student invite `s-familyinvite` | invite token | activate; auto-approved parent↔student link |
| 06 | Instructor dashboard `s-idash` | aggregate counts, today's sessions, pending-grading count | — |
| 07 | Curriculum builder `s-curriculum` | course tree | chapter/lesson CRUD, **reorder (drag at every level)**, publish/draft |
| 08 | Content & assessment hub `s-content` | lesson content | material upload (+access mode), recording, quiz/homework build, publish |
| 09 | Scheduling `s-calendar` | week/month timetable | create/edit session, online↔offline toggle, **recurrence + "this only / this and following"** |
| 10 | Class session view `s-session` | roster for session | attendance bulk-mark, end session & save |
| 11 | Roster & performance `s-roster` | per-student attendance %, last quiz %, homework state; filters by section/status | — |
| 12 | Fees & revenue `s-fees` | monthly revenue, outstanding, per-student status | send payment reminder → parent notification |
| 13 | Instructor settings `s-isettings` | profile, TA list w/ scope+permissions, billing | invite/edit/revoke TA |
| 14 | TA dashboard `s-tadash` | assigned groups, pending count, today's sessions | — |
| 15 | Grading queue `s-grading` | ungraded **structured** answers only (MCQ auto-graded) | score + comment per answer, upload solutions |
| 16 | Attendance taking `s-attendance` | session roster | save attendance |
| 17 | Parent home `s-phome` | children summary cards, notification feed | — |
| 18 | Child detail `s-pchild` | attendance / grades / fees / schedule tabs | fee payment only |
| 19 | Student dashboard `s-shome` | next session (+join window), due-soon across all courses, recent grades | — |
| 20 | Lesson & materials `s-lesson` | published lessons + files + recordings | **view/open logs a "viewed" state** |
| 21 | Live class `s-liveclass` | embedded meeting | auto-attendance on join; early leave → partial |
| 22 | Quiz taking `s-quiz` | questions, **timer**, navigator | answer save, submit (MCQ scored immediately, rest pending) |
| 23 | Homework submission `s-homework` | assignment + deadline | file + note submit; late flag; **re-submit until graded, then locked** |

### Derived/aggregate values with no column behind them
These must be computed server-side and documented as response fields, not stored: dashboard stat cards (`WF #s-idash`), attendance % and average grade per student (`WF #s-roster`, `#s-phome`), "paid on time %" (`WF #s-fees`), pending-grading counts (`WF #s-idash`, `#s-tadash`), lesson progress `Done / In progress` (`WF #s-lesson`).

---

## 6. Real-time / propagation contract

`SCOPE §3.C` ("Real-Time Synchronization") plus explicit wireframe promises — the API needs a documented push story (SSE or WebSocket) alongside REST:

| Trigger | Immediately visible on | Ref |
|---|---|---|
| "End Session & Save Attendance" | Parent Home badges (17), Child Detail (18) | `WF #s-session`, `#s-attendance` |
| Grade saved in grading queue | Student quiz result (22), Child Detail (18) | `WF #s-grading` |
| Publish material/quiz | Student lesson view (20), Parent Home if graded work (17) | `WF #s-content` |
| Any schedule change | Student dashboard (19), Parent Home (17) | `WF #s-calendar` |
| Parent pays fee | Clears overdue badge on Parent Home | `WF #s-pchild` |
| "Send reminder" | Parent notification | `WF #s-fees` |

`NOTIFICATIONS` (`ERD:98-106`, types `ASSIGNMENT, QUIZ, ANNOUNCEMENT, SYSTEM`) is the persistence layer for the Parent Home "Recent updates" feed and reminders.

---

## 7. Gaps — wireframe/scope needs with no ERD backing

**These must be resolved before the endpoints that depend on them can be specified.** Flagged with a recommendation; none are yet decided.

| # | Gap | Evidence | Suggested resolution |
|---|---|---|---|
| ~~G1~~ | ✅ **RESOLVED.** `PARENT` added to `ROLES`; `PARENTS` profile table + `PARENT_STUDENTS (parent_user_id, student_id)` M:N junction added; `STUDENTS.parent_phone` removed | `ERD:31-34`, `ERD:65-74`, `ERD:429-435` | Done. Remaining open question: which linked parent receives a singular notification ("Send reminder", `WF #s-fees`) when a child has more than one |
| ~~G2~~ | ✅ **RESOLVED.** `ENROLLMENT_FEES` + `PAYMENTS` | student × group × monthly period, distinct from `SUBSCRIPTIONS` | `WF #s-fees`, `#s-pchild` |
| ~~G3~~ | ✅ **RESOLVED.** `LESSONS.status DRAFT/PUBLISHED` | `WF #s-curriculum`, `#s-lesson` | — |
| ~~G4~~ | ✅ **RESOLVED.** `INVITES` + `INVITE_GROUPS` | `ERD:76-88`, `ERD:90-96`, `ERD:417-428` | Issuer is a `USERS` fk, not `TEACHERS`, so a student can invite their own parent (WF 05). `INVITE_GROUPS` stores group scope only; TA permission flags are granted after acceptance. Four questions remain open — see `ERD` Open Question 6 |
| ~~G5~~ | ✅ **RESOLVED.** Password-reset OTP in **cache**, not a table | `WF #s-forgot` | Hashed 6-digit code, 10-minute TTL, 5 attempts. Reset body is `email` + `otp` + `password` |
| ~~G6~~ | ✅ **RESOLVED** — three permission booleans + `is_revoked` on `GROUP_ASSISTANTS`. Flags **default false**; granted after the TA accepts (WF 13 Edit), not stored on `INVITE_GROUPS` | `ERD` vs `WF #s-isettings`, `#s-tainvite` | Invite collects section scope; Edit after activation collects attendance / grading / homework upload |
| ~~G7~~ | ✅ **RESOLVED.** `MATERIALS.access_mode`, `size_bytes`, `mime_type` | `WF #s-content` | — |
| ~~G8~~ | **Dropped.** No view-log tables. `max_watch_limit` stays on `RECORDED_SESSIONS` but is not enforced | `WF #s-lesson` | Roster "viewed" and watch caps are out of schema |
| ~~G9~~ | ✅ **RESOLVED** by the assignment/quiz split — **No quiz time limit** despite a countdown timer on the quiz screen | `WF #s-quiz` vs `ERD:247-257` | Add `ASSESSMENTS.duration_seconds` (nullable = untimed) |
| ~~G10~~ | ✅ **RESOLVED.** `SESSION_SERIES` + materialized `LIVE_SESSIONS`; `PATCH ?scope=this\|this_and_following` | `WF #s-calendar` | `D14` still open when later occurrences have attendance |
| ~~G11~~ | ✅ **RESOLVED** — **Submission status conflates lateness with grading.** Enum is `SUBMITTED, GRADED, REJECTED, LATE` — a late-then-graded submission loses its lateness, but the wireframe requires late to stay visible to instructor and parent | `ERD:270-283` vs `WF #s-homework` | Split into `status` + a separate `is_late` boolean |
| ~~G12~~ | ✅ **RESOLVED** for re-submission shape (overwrite in place); lock trigger still open — **No re-submission semantics.** "Re-submission allowed until graded; grading locks it" | `WF #s-homework` vs `ERD:270-283` | Define whether re-submit updates in place or versions; document the lock as `409` after `GRADED` |
| ~~G13~~ | ✅ **RESOLVED.** `ATTENDANCE.status` includes `PARTIAL`; `joined_at` / `left_at` / `recorded_by_user_id` | `WF #s-liveclass` | Manual override wins and stamps `recorded_by` |
| G14 | **"Terms" level missing.** Scope and the builder screen both show subjects → **terms** → chapters → lessons; the ERD is COURSES → CHAPTERS → LESSONS | `SCOPE §3.B`, `WF #s-curriculum` ("IG Physics — Term 1") vs `ERD:127-152` | Confirm term is folded into the course (one course per term) — likely, but state it explicitly in the docs |
| ~~G15~~ | ✅ **RESOLVED.** `meeting_provider` + `external_meeting_id` + webhook | `WF #s-session`, `#s-liveclass` | — |
| ~~G16~~ | ✅ **RESOLVED.** `TEACHERS.curriculum` (`IGCSE` / `AMERICAN_DIPLOMA` / `BOTH`); `COURSES.curriculum` is one track; subjects are a catalog (`SUBJECTS`) | `WF #s-signup`, `#s-phome` | Parent child cards concatenate course curriculum + `SUBJECTS.name` |

---

## 8. Implementation state (`CODE`)

The backend is **scaffolding only** — do not assume any of the ERD exists yet:
- `prisma/schema.prisma` (29 lines) holds a single placeholder `User` model with `Role { STUDENT, INSTRUCTOR, ADMIN }` — **conflicts with the ERD's `TEACHER/STUDENT/ASSISTANT/ADMIN`** (`ERD:31-34`). The ERD wins; the schema must be rewritten.
- `src/` has only health routes, error/logging middleware, and config. No domain controllers, services or routes exist.
- Stack: Express 5, TypeScript (ESM), Prisma 7 + `@prisma/adapter-pg` on PostgreSQL, Zod for validation, Helmet + CORS. So: **Zod schemas are the natural home for the §3 service-layer invariants**, and the API docs should be written spec-first, ahead of the implementation.

---

## 9. Conventions to carry into the API documentation

Derived from the above; proposed, to confirm at the next stage:

1. **Resource paths follow the two-branch split** — `/courses/{id}/chapters/{id}/lessons/...` for curriculum, `/groups/{id}/live-sessions|assessments|students` for cohorts. Never nest attendance under a lesson.
2. **UUID `id`s everywhere**, ISO-8601 UTC timestamps, `decimal` money/score as string to avoid float loss.
3. **Auth**: JWT access token + refresh-token rotation backed by `USER_SESSIONS` (`ERD:41-50`) which stores `refresh_token_hash`, `user_agent`, `ip_address`, `is_revoked` — so document device listing and per-session revoke.
4. **Every endpoint carries a role matrix row** (instructor / TA+permission / parent / student) plus the ownership scope check (own course, assigned group, linked child, own enrollment).
5. **Consistent list envelope**: pagination, plus the filters the roster and calendar screens demand (`section`, `status`, date range).
6. **Bulk endpoints are first-class**, not an afterthought — "mark all present" (`WF #s-session`), reorder chapters/lessons (`WF #s-curriculum`), bulk grade save. Ahmed's persona goal is speed at 150+ students.
7. **Errors**: one problem-shape with a machine code; the §3 invariants and the CHECK constraints each get a named code.
8. **Auth responses never leak account existence** (`WF #s-forgot`).
