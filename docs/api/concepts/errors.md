# Errors

## One shape

Every failure returns the same body, with a stable machine-readable `code`:

```json
{
  "error": {
    "code": "LESSON_COURSE_MISMATCH",
    "message": "The lesson does not belong to this group's course.",
    "details": [
      { "field": "lesson_id", "issue": "cross_course_reference" }
    ]
  }
}
```

`message` is for humans and may change. `code` is the contract — branch on it, not on the message
or the status.

## Status codes

| Status | Meaning |
|---|---|
| `400` | Malformed body or parameters |
| `401` | Missing, invalid or expired access token |
| `403` | Authenticated, but wrong role, ownership scope or permission flag |
| `404` | No such resource, or the caller may not see it |
| `409` | Conflict with current state — uniqueness, a lock, or a `RESTRICT` delete |
| `410` | Token expired or already used |
| `422` | Well-formed but violates a schema invariant |

## Cross-branch invariants — `422`

| Code | Raised by |
|---|---|
| `LESSON_COURSE_MISMATCH` | Creating or updating a live session whose `lesson_id` is outside the group's course |
| `RECORDING_SESSION_MISMATCH` | A recording whose source live session covers a different lesson |
| `QUIZ_COURSE_MISMATCH` | A quiz whose `lesson_id` tag is outside the group's course |

## Field constraints — `422`

| Code | Rule |
|---|---|
| `MEETING_URL_REQUIRED` | `mode = ONLINE` requires a meeting URL |
| `CLASSROOM_REQUIRED` | `mode = ONSITE` requires a classroom location |
| `INVALID_TIME_RANGE` | `scheduled_end > scheduled_start` |
| `INVALID_QUIZ_WINDOW` | `closes_at > opens_at` |
| `INVALID_QUIZ_DURATION` | `duration_seconds > 0` when set; omit for untimed |
| `INVALID_WATCH_LIMIT` | `max_watch_limit >= 0`, where **0 means unlimited** |
| `SOLUTION_BEFORE_DEADLINE` | `solution_released_at >= due_date` — releasing answers early defeats the assignment |
| `POINTS_EXCEED_QUESTION` | `0 <= points_awarded <= question.points` |
| `NOT_MANUALLY_GRADABLE` | A human grade was submitted for an `MCQ` answer |

## Uniqueness — `409`

| Code | Constraint |
|---|---|
| `ORDER_INDEX_CONFLICT` | Ordering within a course, chapter, lesson or quiz |
| `ATTENDANCE_ALREADY_RECORDED` | One attendance row per student per session |
| `RECORDING_ALREADY_LINKED` | At most one recording per live class |
| `ATTEMPT_ALREADY_EXISTS` | One attempt per student per quiz — retakes are not modelled |

## State — `409`

| Code | Rule |
|---|---|
| `GROUP_HAS_HISTORY` | Cohorts with sessions or quizzes are archived, never deleted |
| `HAS_STUDENT_WORK` | An assignment with submissions, or a quiz with attempts, cannot be deleted |
| `SUBMISSION_LOCKED` | Re-submission after the lock trigger |
| `ATTEMPT_EXPIRED` | Answer save after the attempt's `expires_at` |
| `ATTEMPT_INCOMPLETE` | Finalize called before every structured answer is scored |
| `JOIN_WINDOW_CLOSED` | Join attempted outside the session's window |
| `GROUP_AT_CAPACITY` | Enrollment past `max_capacity` |

## Auth

| Code | Status | Note |
|---|---|---|
| `INVALID_CREDENTIALS` | `401` | Never distinguishes an unknown email from a wrong password |
| `TOKEN_EXPIRED` | `401` | Also used for invite and reset links |
| `INSUFFICIENT_SCOPE` | `403` | Right role, wrong ownership — or a TA missing the permission flag |

{% hint style="warning" %}
`POST /auth/password/forgot` returns `202` unconditionally and raises nothing. Leaking whether an
address has an account is the failure mode there, so a missing account is not an error.
{% endhint %}
