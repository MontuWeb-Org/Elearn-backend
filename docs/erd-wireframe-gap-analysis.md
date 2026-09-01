# ERD ↔ Wireframe Gap Analysis

A findings list only — no proposed fixes. Ref keys: `ERD` = `docs/erd.md` (line numbers), `WF` = `docs/elearning-platform-wireframes.html` (screen number + `id`), `SCOPE` = `docs/Montu - E-Learning Platform.md`.

---

## A. UI functionality with no obvious database representation

| # | UI functionality | Where in UI | ERD state |
|---|---|---|---|
| A1 | Parent tier as a whole — parent account, parent↔child link, multi-child switcher, parent-side login | `WF 05 s-familyinvite`, `17 s-phome`, `18 s-pchild`; `SCOPE §3.A` | `ROLES` enum is `TEACHER, STUDENT, ASSISTANT, ADMIN` (`ERD:29-32`); the only parent trace is `STUDENTS.parent_phone`, a plain string (`ERD:56-62`) |
| A2 | Student fee status (Paid / Overdue), per-student "Plan" column (Monthly), receipts, "Send reminder", parent-side payment | `WF 12 s-fees`, `18 s-pchild` | No payment, invoice, or fee-schedule entity. `COURSES.fees` is one static decimal (`ERD:93-102`); `SUBSCRIPTIONS` is instructor→platform (`ERD:83-91`) |
| A3 | Revenue aggregates — "This month", "Outstanding", "Paid on time 91%" | `WF 12 s-fees` | No transaction data of any kind |
| A4 | Invite issuance and activation — TA invite, parent/student invite, invite token, scope shown on the invite page, activation | `WF 04 s-tainvite`, `05 s-familyinvite`, `13 s-isettings` | No invite entity or token store |
| A5 | Password reset link, expiry window, expired-link resend | `WF 03 s-forgot` | No reset-token entity |
| A6 | TA permission model — per-section scope ("All sections" / "Section A only") **and** per-action permissions (attendance / grading / homework upload), set at invite time, editable, revocable without deleting grading history | `WF 13 s-isettings`, `04 s-tainvite` | `GROUP_ASSISTANTS` is a bare composite-PK join with no permission or scope columns (`ERD:152-156`) |
| A7 | Lesson `Published` / `Draft` state gating student and parent visibility | `WF 07 s-curriculum`, `20 s-lesson` | `LESSONS` has no status field (`ERD:112-118`); status exists only on `COURSES` (`ERD:93-102`) |
| A8 | Per-file access mode — view-only vs downloadable, set at upload | `WF 08 s-content` | `MATERIALS` has title / file_url / uploaded_at only (`ERD:134-141`) |
| A9 | File metadata shown in the materials list — size ("1.2 MB"), file type icon | `WF 08 s-content` | No size or MIME on `MATERIALS` |
| A10 | Engagement tracking — "opening a file logs a viewed state the instructor can see on the roster"; per-lesson `Done` / `In progress` progress chips | `WF 20 s-lesson`, `11 s-roster` | No view/progress table. The ERD states enforcement of `max_watch_limit` "lives in the application (or is deferred)" and names a `RECORDED_SESSION_VIEWS` log as a future extension (`ERD:337-345`) |
| A11 | Quiz countdown timer ("⏱ 08:42 remaining") | `WF 22 s-quiz` | `ASSESSMENTS` has no duration/time-limit field (`ERD:185-194`) |
| A12 | In-progress quiz attempt — question navigator, jumping between answered/unanswered, state before final submit | `WF 22 s-quiz` | `ASSESSMENT_SUBMISSIONS` models only a completed submission (`submitted_at`, no start/attempt state) (`ERD:205-215`) |
| A13 | Recurring sessions set weekly per section; editing one occurrence prompts "this session only" vs "this and following" | `WF 09 s-calendar` | `LIVE_SESSIONS` rows are independent; `GROUPS.schedule_info` is a free-text hint explicitly described as a default, not truth (`ERD:143-151`, `ERD:337-345`) |
| A14 | Video-conferencing integration — auto-generate a Zoom/Meet link "if connected", read the tool's join log, embed the session in-app | `WF 09 s-calendar`, `10 s-session`, `21 s-liveclass` | Only `LIVE_SESSIONS.meeting_url`, a plain nullable string (`ERD:162-174`). No provider, credential, or external-meeting-id representation |
| A15 | Join window — "Join Now only activates within the join window of a scheduled session; otherwise shows countdown" | `WF 19 s-shome` | No join-window or early-join field |
| A16 | Partial attendance — "leaving early can flag partial attendance" | `WF 21 s-liveclass` | `ATTENDANCE.status` is `PRESENT, ABSENT, LATE` with no partial value and no join/leave timestamps (`ERD:176-183`) |
| A17 | Late flag that persists next to a grade and stays visible to instructor and parent | `WF 23 s-homework`, `11 s-roster`, `18 s-pchild` | `LATE` is one value in the same enum as `GRADED` on `ASSESSMENT_SUBMISSIONS` (`ERD:205-215`) |
| A18 | Re-submission until graded; grading locks the submission | `WF 23 s-homework` | No attempt/version or lock representation |
| A19 | "Upload homework solutions" by the TA — solution files attached to an assessment | `WF 15 s-grading` | `ASSESSMENTS` has no attachment or solution field (`ERD:185-194`) |
| A20 | Student's optional "Notes for your teacher" attached to a homework submission | `WF 23 s-homework` | `ASSESSMENT_SUBMISSIONS.feedback_comments` is grader-side; no student-authored note field |
| A21 | Instructor sign-up captures full name as one field, "Subject(s) taught" (plural), and curriculum choice IGCSE / American Diploma / **Both** | `WF 02 s-signup` | `USERS` splits `first_name`/`last_name`; `TEACHERS.specialization` is a single string; no curriculum field anywhere (`ERD:17-27`, `ERD:50-55`) |
| A22 | "Remember me" on login | `WF 01 s-login` | No representation of session lifetime choice on `USER_SESSIONS` (`ERD:39-49`) |
| A23 | Notification deep-links — "tapping an update deep-links to the specific session or quiz" | `WF 17 s-phome` | `NOTIFICATIONS` has title/message/type only, no target entity type or id (`ERD:64-73`) |
| A24 | Per-student detail panel showing full history **plus linked parent contact** | `WF 11 s-roster` | Depends on A1 |
| A25 | Avatars / instructor logo / display names in the app chrome and greetings | `WF 06 s-idash`, `13 s-isettings`, `14 s-tadash` | No avatar or display-name field on `USERS` |
| A26 | Student "Profile" section in the student nav | `WF 19 s-shome` | No student-editable profile fields defined |

---

## B. Database entities and fields with no apparent UI usage

| # | Entity / field | ERD ref | Observation |
|---|---|---|---|
| B1 | `ADMIN` role | `ERD:29-32` | No admin screen exists among the 24; the wireframe covers four tiers only, and `SCOPE §3.A` names the same four |
| B2 | `SUBSCRIPTION_PLANS` (`max_students`, `billing_period`), `SUBSCRIPTIONS` (`status`, `start_date`, `end_date`) | `ERD:75-91` | Surface only implicitly as sign-up steps 2–3 and a "Billing" tab label (`WF 02 s-signup`, `13 s-isettings`); no screen shows or edits plan limits or subscription state |
| B3 | `USER_SESSIONS` (`user_agent`, `ip_address`, `is_revoked`, `expires_at`) | `ERD:39-49` | No device/session management screen; nothing lists or revokes sessions |
| B4 | `NOTIFICATIONS.type` values `ANNOUNCEMENT`, `SYSTEM` | `ERD:64-73` | No authoring UI for announcements; the only feed (`WF 17 s-phome`) shows attendance and grade events |
| B5 | `RECORDED_SESSIONS.publish_at`, `deadline`, `max_watch_limit`, `duration_seconds`, `order_index` | `ERD:120-132` | No screen sets these; the student lesson view shows an undifferentiated "🎬 Recording" link (`WF 20 s-lesson`). `duration_seconds` may back the "(42 min)" label in `WF 08 s-content` |
| B6 | `RECORDED_SESSIONS.recorded_from_live_session_id` | `ERD:120-132` | No UI links a recording back to the live class it came from, and no screen shows a session's recording after the fact |
| B7 | `STUDENTS.student_code`, `school_name`, `grade_level` | `ERD:56-62` | Never captured (student invite asks only for a password, `WF 05 s-familyinvite`) and never displayed |
| B8 | `USERS.age`, `is_active`, `date_joined`, `last_login_at` | `ERD:17-27` | Not captured or displayed on any screen |
| B9 | `TEACHERS.bio` | `ERD:50-55` | No instructor public profile screen |
| B10 | `COURSES.course_code`, `description`, `grade_level`, `status DRAFT/ACTIVE/ARCHIVED` | `ERD:93-102` | The builder shows the chapter/lesson tree only (`WF 07 s-curriculum`); course-level status never appears |
| B11 | `CHAPTERS.description`, `LESSONS.description` | `ERD:104-118` | Not present in any layout |
| B12 | `GROUPS.max_capacity` | `ERD:143-151` | No enrollment cap, "group full", or capacity indicator anywhere |
| B13 | `GROUPS.schedule_info`, `GROUPS.classroom_location` | `ERD:143-151` | The calendar renders from live sessions; the group's default pattern is never shown or edited |
| B14 | `LIVE_SESSIONS.status = CANCELLED` | `ERD:162-174` | No cancel action and no cancelled state in the calendar (`WF 09 s-calendar`) |
| B15 | `ASSESSMENT_SUBMISSIONS.status = REJECTED` | `ERD:205-215` | Nothing in the grading or submission flow rejects a submission |
| B16 | `ASSESSMENT_QUESTIONS.question_type` values `ESSAY`, `TEXT`, `FILE_UPLOAD` | `ERD:195-203` | The quiz builder distinguishes only MCQ vs "structured answer" (`WF 08 s-content`, `15 s-grading`); no UI selects among the three non-MCQ types |
| B17 | `ASSESSMENT_QUESTIONS.model_answer` | `ERD:195-203` | Not shown to the grader in the grading queue |
| B18 | `ASSESSMENT_SUBMISSION_ANSWERS.evaluator_comment` (per answer) vs `ASSESSMENT_SUBMISSIONS.feedback_comments` (per submission) | `ERD:205-231` | The grading UI shows a score box per answer only; neither comment field has a visible input |
| B19 | `ASSESSMENTS.max_score` | `ERD:185-194` | Grading is shown per-question ("2 pts"), roster shows percentages; the assessment-level max is never displayed |
| B20 | `ATTENDANCE.status = LATE` | `ERD:176-183` | Both attendance screens are binary Present/Absent toggles with a "Mark all present" bulk action (`WF 10 s-session`, `16 s-attendance`) |
| B21 | `ROLES` / `USER_ROLES` as a many-to-many | `ERD:29-38` | Every screen assumes one role per user; login routes to a single destination and no role switcher exists (`WF 01 s-login`) |
| B22 | `LESSONS ||--o{ ASSESSMENTS` (`ASSESSMENTS.lesson_id`, "tagging only") | `ERD:185-194` | Partially used — quizzes are authored in lesson context (`WF 08 s-content`) — but no screen ever shows or filters assessments by lesson tag |
| B23 | `NOTIFICATIONS.is_read` | `ERD:64-73` | The parent feed shows no read/unread distinction; no other screen has a notification centre |

---

## C. Information the UI requires that cannot currently be obtained from the ERD

| # | Required value | Where displayed | Why it is unobtainable |
|---|---|---|---|
| C1 | "Paid on time 91%", "This month", "Outstanding" | `WF 12 s-fees` | No payment data exists (see A2) |
| C2 | Fee badge per child ("Fee overdue") | `WF 17 s-phome`, `18 s-pchild` | Same |
| C3 | The four dashboard KPI numbers (158 / 6 / 4 / 12) | `WF 06 s-idash` | Their **labels are blank placeholder bars in the wireframe source**; only the deep-link note names three targets (roster, courses, schedule), leaving the fourth metric undefined. The values cannot be sourced without knowing what they count |
| C4 | Homework state per student: `Submitted` / `Late` / `Missing` | `WF 11 s-roster` | "Missing" is the absence of a submission row; deriving it requires a defined per-student expected-assessment set and a deadline-passed rule that the ERD does not encode |
| C5 | Per-lesson progress `Done` / `In progress` | `WF 20 s-lesson` | No per-student lesson or material progress data (see A10) |
| C6 | "Opening a file logs a viewed state the instructor can see on the roster" | `WF 20 s-lesson`, `11 s-roster` | Same; and the roster has no column for it |
| C7 | Linked parent contact on the student detail panel | `WF 11 s-roster` | No parent entity (A1) |
| C8 | Quiz time remaining | `WF 22 s-quiz` | Requires both an attempt start timestamp and a duration; neither exists (A11, A12) |
| C9 | "MCQs auto-graded — 18/24 already complete" | `WF 15 s-grading` | Requires per-question grading progress across submissions; `total_score` is a single nullable value on the submission |
| C10 | "MCQ score shows immediately; overall grade stays pending until a human grades it" | `WF 22 s-quiz` | Requires a partial/provisional score distinct from the final `total_score` |
| C11 | File size ("1.2 MB") and type | `WF 08 s-content` | Not stored (A9) |
| C12 | Curriculum label on a parent's child card ("IG Physics", "American Diploma Math") | `WF 17 s-phome` | No curriculum field; `COURSES.grade_level` is free text (A21) |
| C13 | A single "Section" per student row | `WF 11 s-roster`, `12 s-fees` | `STUDENT_GROUPS` is many-to-many, so a student may map to several groups; the UI assumes one |
| C14 | The roster for a past session ("Attendance (24)") | `WF 10 s-session` | Group membership is current-state only; a past session's roster would be reconstructed from present membership, which drifts as students join or leave |
| C15 | TA's "Today's sessions to cover" | `WF 14 s-tadash` | `GROUP_ASSISTANTS` assigns a TA to a group, not to a session; "to cover" implies a per-session assignment that does not exist |
| C16 | Attendance % and average grade per student | `WF 11 s-roster`, `17 s-phome`, `18 s-pchild` | Computable in principle, but the denominator is undefined — see D5, D15 |
| C17 | "Needs grading — 24 pending" across all sections | `WF 06 s-idash`, `14 s-tadash` | Computable only once "pending" is defined (see D18) |
| C18 | Relative timestamps and targets in the parent activity feed | `WF 17 s-phome` | `NOTIFICATIONS` has `created_at` but no target reference for the deep-link (A23) |
| C19 | Currency on any monetary figure | `WF 12 s-fees`, `02 s-signup` | No currency field on `COURSES.fees` or `SUBSCRIPTION_PLANS.price` |

---

## D. Ambiguous behaviors

| # | Ambiguity | Evidence |
|---|---|---|
| D1 | A quiz is authored **inside a lesson** in the Content & Assessment Hub, but `ASSESSMENTS.group_id` is mandatory and no screen asks which group(s) the quiz is for. Whether publishing fans out one assessment per group, or creates a single shared one, is undefined | `WF 08 s-content` vs `ERD:185-194` |
| D2 | Relationship between lesson `Published`/`Draft` and per-item publishing ("Publishing from any tab here instantly reflects…") — whether a published material inside a draft lesson is visible | `WF 07 s-curriculum`, `08 s-content` |
| D3 | "Section" vs "Group" vs course: is "IG Physics — Revision" a third group of the IG Physics course, or a separate course? It appears both as a section filter chip and as a class in the calendar | `WF 06 s-idash`, `09 s-calendar`, `11 s-roster`, `14 s-tadash` |
| D4 | Whether a student may belong to more than one group of the same course | `ERD:157-161` allows it; `WF 11 s-roster` shows one section per student |
| D5 | Auto-marked vs manually overridden attendance — which wins, when reconciliation happens, and who recorded a value (`ATTENDANCE` has no `recorded_by`) | `WF 10 s-session`, `21 s-liveclass` vs `ERD:176-183` |
| D6 | What "partial attendance" resolves to when a student leaves early | `WF 21 s-liveclass` |
| D7 | Re-submission semantics: a new row per attempt or an overwrite; whether lateness is re-evaluated on each attempt | `WF 23 s-homework` |
| D8 | A submission can be both late and graded, but `LATE` and `GRADED` are values of the same enum | `WF 23 s-homework` vs `ERD:205-215` |
| D9 | Who may regrade after a TA grades, and whether grading is reversible — `graded_by_user_id` is a single field, and grading "locks" the submission | `WF 15 s-grading`, `23 s-homework` |
| D10 | TA scope "All sections" — whether it auto-includes groups created later, and how it is represented against a per-group join table | `WF 13 s-isettings` vs `ERD:152-156` |
| D11 | Whether a TA may serve more than one instructor, and whether the grading queue can span instructors | `WF 14 s-tadash`, `15 s-grading` |
| D12 | Parent linking is "auto-approved for the instructor's classes, no manual matching" — the approval semantics, and whether a parent sees only that instructor's classes or everything about the child | `WF 05 s-familyinvite` |
| D13 | One parent linked to children across multiple instructors — what isolation, if any, exists between instructors' data | `WF 01 s-login`, `05 s-familyinvite`, `17 s-phome` |
| D14 | Editing a recurring session with "this and following" when attendance has already been recorded on later occurrences | `WF 09 s-calendar` |
| D15 | Whether cancelled sessions count toward attendance percentages, and whether cancellation notifies students and parents | `ERD:162-174` (`CANCELLED` exists) vs `WF 09 s-calendar` (no cancel UI) |
| D16 | Whether sessions with no lesson (revision, exam prep, Q&A) appear anywhere in the student's lesson view or count toward progress | `ERD:337-345`, `WF 09 s-calendar`, `20 s-lesson` |
| D17 | Quiz timer expiry — auto-submit, lock, or grace | `WF 22 s-quiz` |
| D18 | Status of a mixed MCQ/structured submission between auto-grading and human grading, and what "pending" counts in the dashboard badge | `WF 15 s-grading`, `22 s-quiz`, `06 s-idash` |
| D19 | Fee cadence: the fees table has a per-student "Plan: Monthly" column while `COURSES.fees` is a single decimal — whether fees are per course, per group, per month, or per student | `WF 12 s-fees` vs `ERD:93-102` |
| D20 | Sign-up step 2 sets the plan "based on student count and **TA seats**", but `SUBSCRIPTION_PLANS` has only `max_students` — whether TAs consume seats | `WF 02 s-signup` vs `ERD:75-82` |
| D21 | How view-only material access is enforced (streamed, signed URL, DRM) and whether recordings are hosted or externally linked | `WF 08 s-content` vs `ERD:120-141` (plain URL fields) |
| D22 | Notification delivery channel — in-app only, or email/push, given the parent tier is framed as a mobile app and "Send reminder" implies outbound contact | `WF 12 s-fees`, `17 s-phome` |
| D23 | The mechanism behind "instantly" / "in real time" (polling, SSE, WebSocket) is asserted on six flows but never specified | `SCOPE §3.C`; `WF 08, 09, 10, 15, 16, 17, 18` |
| D24 | Timezone handling — whose timezone a session time renders in for students and parents | `WF 09 s-calendar`, `17 s-phome`, `19 s-shome` |
| D25 | Whether the instructor's Session View and the TA's Attendance screen are the same capability with identical rights ("same attendance component") or differ in what can be overridden | `WF 10 s-session` vs `16 s-attendance` |
| D26 | Deletion vs archival: no screen offers deleting a course, group, or student, while the ERD defines `RESTRICT` on groups and `CASCADE` down the curriculum | `ERD:322-335` |
| D27 | Multi-role users (`USER_ROLES` is M:N) versus a login that routes to exactly one home screen | `ERD:34-38` vs `WF 01 s-login` |
| D28 | Whether a student is enrolled in a *course* or only in a *group*, and whether course-level enrollment without a group is possible | `ERD:157-161` |
| D29 | "Homework" appears as its own tab and nav item, distinct from quizzes, while the ERD models both as `ASSESSMENTS.type` | `WF 08 s-content`, `19 s-shome` vs `ERD:185-194` |
| D30 | Whether the instructor can see or act on everything a TA can ("Instructor can see everything a TA does") including editing TA-entered grades and attendance | `WF 14 s-tadash` |
| D31 | Revoking a TA "immediately removes access without deleting grading history" — the state of a revoked assistant row and of in-flight grading | `WF 13 s-isettings` vs `ERD:152-156` |
| D32 | What curriculum "Both" means for a teacher, and whether curriculum is a property of the teacher, the course, or the group | `WF 02 s-signup` |

---

## E. Assumptions that would be required to design the API

Each of these must be adopted (or replaced by a decision) before endpoints can be specified. They are stated as assumptions, not recommendations.

**Structural**
1. The wireframe's "section" is the ERD's `GROUPS` row; "class" in the calendar is a `LIVE_SESSIONS` row.
2. "Term" (`SCOPE §3.B`, `WF 07` "IG Physics — Term 1") has no entity; a term is folded into a course or into its name.
3. Wireframe role names map to ERD roles as Instructor → `TEACHER`, TA → `ASSISTANT`; the parent tier has no role value to map to.
4. Curriculum content (`CHAPTERS`/`LESSONS`/`MATERIALS`/`RECORDED_SESSIONS`) is shared identically by every group of a course, and students reach it only through a group they are enrolled in.
5. A student belongs to at most one group per course, so a single "Section" label is well defined.
6. Attendance exists only against a `LIVE_SESSIONS` row — there is no course-level, day-level, or lesson-level attendance.
7. Group membership is current-state; there is no enrollment history, so historical rosters are inferred.
8. Deletion is archival for cohorts and cascading for curriculum, per `ERD:322-335`, and the API exposes no hard delete for groups.

**Behavioral**
9. Publishing an assessment authored in lesson context targets one or more explicitly chosen groups.
10. Publish/draft gating is decided at the lesson level and applies to that lesson's attached materials and recordings.
11. All dashboard, roster, and parent percentages are computed on read and never stored.
12. Grading is idempotent per answer and the most recent grader replaces `graded_by_user_id`.
13. MCQ auto-grading happens at submission time; a mixed assessment stays ungraded overall until every structured answer has a score.
14. `max_watch_limit`, `publish_at`, and `deadline` on recordings are declarative and unenforced in this pass — the ERD says so explicitly (`ERD:337-345`).
15. Cancelled sessions are excluded from attendance denominators.

**Platform**
16. Authentication is an access token plus a refresh token stored as `USER_SESSIONS.refresh_token_hash`; "Remember me" affects refresh lifetime only.
17. A user has exactly one role for routing purposes even though `USER_ROLES` is many-to-many.
18. Files are stored externally and the ERD holds URLs only; upload transport is a separate concern from the resource APIs.
19. Meeting links are opaque URLs — the platform does not hold provider credentials, so auto-generated links and join-log-driven attendance are out of scope until an integration is modeled.
20. Notifications are in-app persisted records; email/push delivery is out of scope.
21. All timestamps are stored UTC and rendered per viewer.
22. A single implied currency is used everywhere.
23. Only instructors self-register; every other account originates from an instructor-issued invite.
24. Scores are absolute against `ASSESSMENTS.max_score`, with percentages derived on read.
