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
| `410` | Invite token or password-reset OTP expired, used, or locked |
| `422` | Well-formed but violates a schema invariant |

## Cross-branch invariants — `422`

| Code | Raised by |
|---|---|
| `LESSON_COURSE_MISMATCH` | Creating or updating a live session whose `lesson_id` is outside the group's course |
| `RECORDING_SESSION_MISMATCH` | A recording whose source live session covers a different lesson |
| `QUIZ_COURSE_MISMATCH` | A quiz whose `lesson_id` tag is outside the group's course |
| `SUBJECT_CURRICULUM_MISMATCH` | A `subject_id` whose catalog curriculum is not allowed by the teacher's or course's curriculum |
| `CURRICULUM_NOT_ALLOWED` | `COURSES.curriculum` is not allowed by `TEACHERS.curriculum` |

## Field constraints — `422`

| Code | Rule |
|---|---|
| `MEETING_URL_REQUIRED` | `mode = ONLINE` requires a meeting URL |
| `CLASSROOM_REQUIRED` | `mode = ONSITE` requires a classroom location |
| `INVALID_TIME_RANGE` | `scheduled_end > scheduled_start` |
| `INVALID_QUIZ_WINDOW` | `closes_at > opens_at` |
| `INVALID_QUIZ_DURATION` | `duration_seconds > 0` when set; omit for untimed |
| `INVALID_MAX_ATTEMPTS` | `max_attempts >= 1` |
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
| `ATTEMPT_IN_PROGRESS` | Student already has an `IN_PROGRESS` attempt on this quiz — resume it |
| `ATTEMPT_LIMIT_REACHED` | Student has used `max_attempts` on this quiz |

## State — `409`

| Code | Rule |
|---|---|
| `GROUP_HAS_HISTORY` | Cohorts with sessions or quizzes are archived, never deleted. Same for deleting a course that still has groups |
| `HAS_STUDENT_WORK` | An assignment with submissions, or a quiz with attempts, cannot be deleted |
| `SUBMISSION_LOCKED` | Re-submission after the lock trigger |
| `ATTEMPT_EXPIRED` | Answer save after the attempt's `expires_at` (auto-submit has already run) |
| `ATTEMPT_INCOMPLETE` | Finalize called before every structured answer is scored |
| `JOIN_WINDOW_CLOSED` | Join attempted outside the session's window |
| `GROUP_AT_CAPACITY` | Enrollment past `max_capacity` |

## Auth

| Code | Status | Note |
|---|---|---|
| `UNAUTHENTICATED` | `401` | Missing, malformed, expired, or revoked access token |
| `INVALID_CREDENTIALS` | `401` | Login, refresh, or existing-account invite accept — never distinguishes unknown email from a wrong password |
| `INVALID_OTP` | `401` | Wrong reset code, or no matching account — never distinguished |
| `OTP_EXPIRED` | `410` | Reset code expired, already used, or locked after too many attempts |
| `ACCOUNT_DISABLED` | `403` | Password matched, `USERS.is_active` is false |
| `EMAIL_TAKEN` | `409` | Register (or a create-on-accept race) against an existing address |
| `FIELD_NOT_ALLOWED` | `422` | Profile field this role cannot write |
| `INSUFFICIENT_SCOPE` | `403` | Right role, wrong ownership — or a TA missing the permission flag |

## Invites

| Code | Status | Note |
|---|---|---|
| `INVITE_INVALID` | `410` | Unknown, expired, rescinded, spent, or empty-scope token. **Never 404** |
| `INVITE_NOT_PENDING` | `409` | Rescind of an invite that is already accepted or already rescinded |
| `GROUPS_REQUIRED` | `422` | Assistant or student invite with no `group_ids` |
| `GROUPS_NOT_ALLOWED` | `422` | Parent invite with `group_ids` |
| `LINKED_STUDENT_REQUIRED` | `422` | Parent invite missing `linked_student_id` |
| `ALREADY_LINKED` | `409` | Parent already linked to that child |
| `INSTRUCTOR_CANNOT_ACCEPT_INVITE` | `409` | A `TEACHER` account presented a TA, student, or parent invite |

{% hint style="warning" %}
`POST /auth/password/forgot` returns `202` unconditionally and raises nothing. Leaking whether an
address has an account is the failure mode there, so a missing account is not an error.
{% endhint %}
