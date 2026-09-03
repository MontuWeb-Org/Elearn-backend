# Invites

Every account except an instructor's arrives through an invite. The instructor issues one (name + email + scope), the
recipient opens a public preview showing exactly what access they are being granted, and accepting
creates the account with that scope already applied. `INVITES.full_name` is the name the issuer typed; student and parent setup screens collect only a password, so that column is what lands on `USERS.full_name`. A TA may override it on WF 04.

{% hint style="info" %}
5 operations — **all ready**. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}

{% hint style="info" %}
**The public endpoints live under `/invite-tokens`, not `/invites`.** `/invites/{inviteId}` and
`/invites/{token}` are indistinguishable to a router. Splitting them also separates the
authenticated management surface from the public one.
{% endhint %}

## Implementation contract

### Issuer

`INVITES.issued_by_user_id` references `USERS`, not `TEACHERS`. **A student may invite their own parent.**

| Caller | Allowed `role` | Scope |
|---|---|---|
| Instructor | `ASSISTANT`, `STUDENT`, `PARENT` | Every `group_id` must belong to a course the instructor owns. For `PARENT`, `linked_student_id` must be a student enrolled in one of those courses |
| Student | `PARENT` only | `linked_student_id` **must equal the caller**. Anything else is `403 INSUFFICIENT_SCOPE` |

`TEACHER` is never invitable.

### Scope rows

`INVITE_GROUPS` stores which groups. It does **not** carry permission flags.

| Role | Body | Acceptance writes |
|---|---|---|
| `ASSISTANT` | `group_ids` — at least one | `GROUP_ASSISTANTS` rows, all three flags **false** |
| `STUDENT` | `group_ids` — at least one | `STUDENT_GROUPS` rows plus a `STUDENTS` profile if the user is new |
| `PARENT` | no groups; `linked_student_id` required | `PARENT_STUDENTS` plus a `PARENTS` profile if the user is new |

Sending `group_ids` on a `PARENT` invite, or omitting them on `ASSISTANT` / `STUDENT`, is `422`. Codes: `GROUPS_REQUIRED`, `GROUPS_NOT_ALLOWED`, `LINKED_STUDENT_REQUIRED`.

### Token

- Raw token: 32 random bytes, base64url. Exists **only** in the emailed link. Never returned in JSON.
- Stored as `INVITES.token_hash` = SHA-256 hex.
- Default `expires_at` is **now + 7 days**. The issuer may send a later `expires_at`; a past value is `422 INVALID_TIME_RANGE`.
- Preview and accept: any unusable token is **`410 INVITE_INVALID`** — unknown, expired, rescinded, already accepted, or left with zero groups after its sections were archived. Never `404`.

### Re-invite (resend)

There is no separate resend endpoint. `POST /invites` **upserts** the live row matching `(email, role, issued_by_user_id)` where `accepted_at` and `revoked_at` are null:

- Rotates the token (new hash, new email).
- Replaces `full_name`, `expires_at`, and `INVITE_GROUPS`.
- Returns **`200`** when it updated, **`201`** when it created.

An already-accepted or rescinded invite does not block a new one.

### Who may rescind

`DELETE /invites/{inviteId}` stamps `revoked_at` and `revoked_by_user_id`. The row is kept.

| Invite | Who |
|---|---|
| Any, still pending | The issuer |
| Student-issued `PARENT` | The issuing student, **or** an instructor who owns a course that `linked_student_id` is enrolled in |

Rescinding an accepted invite is `409 INVITE_NOT_PENDING`.

### Accept

The **token alone** identifies the invite. The body does not send email. WF 04/05 never ask for it.

`password` is always required (min 8 characters).

| `INVITES.email` already a user? | Behaviour |
|---|---|
| No | Create `USERS` + role + profile. `full_name` is the accept body (TA) or `INVITES.full_name` (student/parent). Insert `USER_SESSIONS`. Return `AuthSession` |
| Yes | Verify `password` against that account. Wrong password is `401 INVALID_CREDENTIALS`. Then **attach**: add the invited role if missing, write the scope rows. `full_name` in the body is ignored |

A `TEACHER` account cannot accept a TA, student, or parent invite: `409 INSTRUCTOR_CANNOT_ACCEPT_INVITE`.

A parent already linked to that child: `409 ALREADY_LINKED`.

Existing-account attach is what lets one parent follow children under two instructors.

Acceptance is one transaction. Then the token is spent (`accepted_at`, `accepted_user_id`).

### Empty scope

If an `ASSISTANT` or `STUDENT` invite has no `INVITE_GROUPS` left at accept time (sections archived, `CASCADE`), treat it as `410 INVITE_INVALID`. Do not create an account with no groups.

### Error codes used here

| Code | Status | When |
|---|---|---|
| `INVITE_INVALID` | 410 | Unknown, expired, rescinded, spent, or empty-scope token |
| `INVITE_NOT_PENDING` | 409 | Rescind of an already accepted/revoked invite |
| `GROUPS_REQUIRED` | 422 | Assistant/student invite with no `group_ids` |
| `GROUPS_NOT_ALLOWED` | 422 | Parent invite with `group_ids` |
| `LINKED_STUDENT_REQUIRED` | 422 | Parent invite missing `linked_student_id` |
| `EMAIL_TAKEN` | 409 | New-account accept when a race created the email first — retry as attach |
| `ALREADY_LINKED` | 409 | Parent already linked to that child |
| `INSTRUCTOR_CANNOT_ACCEPT_INVITE` | 409 | A `TEACHER` account presented a non-teacher invite |
| `INVALID_CREDENTIALS` | 401 | Existing-account accept, wrong password |
| `INSUFFICIENT_SCOPE` | 403 | Student inviting someone other than themselves; instructor scoping a group they do not own |

---

## The issuer is a user, not a teacher

It is also what the invite page renders. *"Mr. Ahmed invited you as a Teaching Assistant"* is a join
from the invite to the issuing user.

## An invited address may already have an account

Do not implement acceptance as "always create user, then link". Look up `INVITES.email` first.

---

## Issue an invite

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/invites" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## List pending invites

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/invites" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Rescind an invite

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/invites/{inviteId}" method="delete" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Preview an invite

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/invite-tokens/{token}" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Accept an invite

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/invite-tokens/{token}/accept" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
