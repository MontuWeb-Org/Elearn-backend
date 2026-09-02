# The two branches

This is the single most important structural fact about the API. Get it wrong and paths end up in
the wrong place; get it right and most resource questions answer themselves.

The schema splits into two branches that meet only at the course:

```
CURRICULUM — authored once, cohort-independent
  /courses/{}/chapters/{}/lessons/{} → /materials
                                     → /recordings
                                     → /assignments/{} → /submissions

COHORTS — per class instance
  /courses/{}/groups/{} → /live-sessions/{} → /attendance
                        → /quizzes/{}       → /questions, /attempts → /answers
```

**Curriculum** is what the instructor writes once. Chapters, lessons, materials, recordings and
assignments are authored against the syllabus and are identical for every group taking the course.

**Cohorts** are the actual classes. A group is a section; a live session is one scheduled class with
its own time and room; a quiz is a timed assessment issued to one group.

## What follows from this

**Attendance is never nested under a lesson.** It records against a `LIVE_SESSIONS` row and nothing
else. There is no course-level, day-level or lesson-level attendance. Two sections covering the
same lesson produce two independent sets of attendance records, because they are two different
classes.

**Materials and recordings are never nested under a group.** They belong to the lesson. A student
reaches them by being enrolled in *some* group of the course, not because the group owns them.

**Students reach curriculum through enrollment,** which is why every student-facing read lives under
`/me/...` rather than `/courses/...`.

## Assignments and quizzes are on different branches

They were once a single entity behind a `type` enum. They are not the same thing and no longer
share a table.

|  | Assignment | Quiz |
|---|---|---|
| Branch | Curriculum | Cohort |
| Attaches to | A **lesson** (structural) | A **group**; lesson id is tagging only |
| Shared across sections | Yes — authored once | No — one quiz per group |
| Timing | A due date | Open/close window plus a per-attempt clock |
| Scored | **Never** | Yes, out of `max_score` |
| Feedback | A released solution file, self-checked | Per-answer scores and comments from a grader |
| Lateness | `is_late` boolean, computed at submission | Not applicable — the window closes |

This is why homework has no grading queue, and why a quiz authored while looking at a lesson still
has to say which section it is for.

## Cross-branch rules

Splitting the branches makes it possible for them to drift apart. Three rules cannot be expressed
as foreign keys and are enforced on write, surfacing as `422`:

1. **`LIVE_SESSIONS.lesson_id`** — when set, the lesson's course must equal the session's group's
   course. A section can only cover lessons from its own course.
2. **`RECORDED_SESSIONS.recorded_from_live_session_id`** — when set, the source class's lesson must
   match the recording's lesson.
3. **`QUIZZES.lesson_id`** — when set, must belong to the group's course.

Assignments need no such rule: they hang off a lesson directly and are therefore natively
cohort-independent.

## Deleting

Deletes follow the branches too. The curriculum spine cascades — deleting a course takes its
chapters, lessons, materials and recordings with it. Two rules override that:

* **Student work is never silently destroyed.** `ASSIGNMENTS → ASSIGNMENT_SUBMISSIONS` and
  `QUIZZES → QUIZ_ATTEMPTS` are `RESTRICT`, so anything with submissions or attempts refuses to
  delete and transitively protects its parents.
* **Attendance history is never destroyed.** `LESSONS → LIVE_SESSIONS.lesson_id` is `SET NULL`.
  Deleting a lesson clears the link on classes that covered it; the classes and their attendance
  survive.

Cohorts are archived, never deleted: `GROUPS → LIVE_SESSIONS` and `GROUPS → QUIZZES` are both
`RESTRICT`, so there is no group delete endpoint at all.
