# Invites

Every account except an instructor's arrives through an invite. The instructor issues one, the
recipient opens a public preview showing exactly what access they are being granted, and accepting
creates the account with that scope already applied.

## The issuer is a user, not a teacher

`INVITES.issued_by_user_id` references `USERS`. That is deliberate: **a student may invite their own
parent.** Wireframe 5 allows the instructor to invite parent and student together, *or* the student
to add a parent later from their own settings. A student may issue only a `PARENT` invite, and only
one linking to themselves.

It is also what the invite page renders. *"Mr. Ahmed invited you as a Teaching Assistant"* is a join
from the invite to the issuing user.

## Scope is a promise of rows

`INVITE_GROUPS` mirrors `GROUP_ASSISTANTS` column for column — the same three permission flags
against the same group ids. Acceptance is therefore a copy rather than a translation, and the scope
stays queryable and foreign-keyed. A JSON blob would happily reference a section that has since been
archived, and the preview page could not render "Section A and Section B" without parsing it.

| Role | Scope means | Acceptance writes |
|---|---|---|
| `ASSISTANT` | Groups plus the three permission flags | `GROUP_ASSISTANTS` rows |
| `STUDENT` | Groups to enroll into; flags ignored | `STUDENT_GROUPS` rows |
| `PARENT` | No groups; `linked_student_id` names the child | One `PARENT_STUDENTS` row |

`TEACHER` is never an invitable role — instructors self-register.

## Tokens

Only `token_hash` is stored, the same treatment as refresh tokens. The raw value exists solely in
the emailed link, so a database leak does not hand the reader a set of working invitations.

A token that is spent, rescinded or expired returns `410`, never `404`. The recipient followed a
real link and should be told it is no longer valid, not that it never existed.

{% hint style="info" %}
**The public endpoints live under `/invite-tokens`, not `/invites`.** `/invites/{inviteId}` and
`/invites/{token}` are indistinguishable to a router. Splitting them also separates the
authenticated management surface from the public one.
{% endhint %}

## An invited address may already have an account

A parent already linked to a child under a *different* instructor accepts by **attaching** — a new
link row on their existing account — not by creating a second one. `accepted_user_id` records which
account the invite resolved to either way.

This is the case that makes one parent account spanning multiple instructors work, and it is easy
to miss when implementing acceptance as "create user, then link".

{% hint style="info" %}
5 operations — **2 ready**, **3** awaiting a decision. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}


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
