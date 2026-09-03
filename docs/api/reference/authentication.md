# Authentication

One login serves all four tiers. The server resolves the caller's role and returns a `routing_target`; the client does not decide where to land.

**Only instructors self-register.** TA, student and parent accounts are always created by an invite — see [Invites](invites.md).

{% hint style="info" %}
12 operations — **all ready**. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}

## Implementation contract

These numbers and rules are part of the API. Do not invent different lifetimes or hash schemes.

### Tokens

| Token | Form | Lifetime | Storage |
|---|---|---|---|
| Access | JWT (`HS256`) | **15 minutes** (`expires_in` is always `900`) | Not stored. Claims: `sub` (user id), `sid` (`USER_SESSIONS.user_session_id`), `roles` (string array), `typ: "access"`, `iat`, `exp` |
| Refresh | Opaque, 32 random bytes, base64url | **7 days**, or **30 days** when `remember_me` is true | `USER_SESSIONS.refresh_token_hash` = SHA-256 hex of the raw token |

Every authenticated request loads the session by `sid` and rejects it if `is_revoked` or `expires_at` is past. Logout and password reset take effect immediately, not at access-token expiry.

Refresh **rotates**: `POST /auth/refresh` hashes the presented token, finds the row, writes a new hash, and returns a new pair. Presenting a rotated or unknown refresh token is `401 INVALID_CREDENTIALS` — never distinguished from a bad login.

`USER_SESSIONS.remember_me` records the checkbox. It only changes refresh lifetime.

### Passwords

- Hash with **bcrypt** (cost 12). Column is `USERS.password_hash`.
- Create/reset/accept require **at least 8 characters**. Login does not re-check length.
- Confirm-password on WF 02 is client-side only; the API takes `password` once.

### Password-reset OTP

Three calls, matching three screens:

1. Email → OTP mailed (SMTP when `SMTP_HOST` is set; development also logs the code)
2. OTP verified → `reset_token`  
3. New password using that token  

| Rule | Value |
|---|---|
| Form | 6 digits, cryptographically random (`000000`–`999999`) |
| Storage | **Cache**, not a table. Key `pwdreset:{userId}` |
| After forgot | Value is SHA-256 hex of the OTP plus an attempt counter |
| After verify | OTP is **deleted**. Value is SHA-256 hex of a one-time `reset_token` |
| TTL | **10 minutes** from forgot; **restarts 10 minutes** on successful verify |
| Attempts | **5** failed OTP checks evict the key |
| New forgot | Replaces the live entry (new OTP, TTL restart, attempts reset). Invalidates any unused `reset_token` |
| `POST /auth/password/forgot` | **Always `202`**. Missing accounts are not distinguishable from sent codes |
| `POST /auth/password/otp/verify` | `email` + `otp` → `{ reset_token, expires_in: 600 }` |
| `POST /auth/password/reset` | `email` + `reset_token` + `password`. Does **not** take the OTP |
| Wrong code / unknown email / bad token | `401 INVALID_OTP` — never distinguished |
| Expired, used, or locked | `410 OTP_EXPIRED` |
| Success | Set the password, **delete the cache key**, **revoke every `USER_SESSIONS` row** for that user |

{% hint style="warning" %}
**Cache is in-process today — Redis later.** OTPs live in the `Map` in `src/config/cache.ts`, not Redis. Restarting the API wipes pending codes. A second instance will not see OTPs issued by the first (verify looks like `410 OTP_EXPIRED`). Before running more than one replica, swap that module for Redis (same `get` / `set` / `update` / `delete`, 10 min TTL). Do not change `password-reset.service.ts`.
{% endhint %}

### Session rows

Login, register, and invite-accept each insert one `USER_SESSIONS` row (`user_agent` and `ip_address` from the request, `remember_me` false unless login sent it).

`GET /me/sessions` lists non-revoked, non-expired rows. `is_current` is true when `sid` matches the caller's access token. `DELETE /me/sessions/{sessionId}` sets `is_revoked`. Revoking the current session is allowed and is equivalent to logout.

### Routing

`routing_target` is derived from `USER_ROLES`, first match in this order: `TEACHER` → `instructor`, `ASSISTANT` → `assistant`, `PARENT` → `parent`, `STUDENT` → `student`.

Inactive users (`is_active = false`) whose password is correct receive `403 ACCOUNT_DISABLED`. Wrong password stays `401 INVALID_CREDENTIALS`.

### Profile writes by role

| Field | Who may PATCH |
|---|---|
| `full_name`, `avatar_url` | All |
| `bio`, `subject_ids` / `subjects`, `curriculum` | Instructor only |
| `phone` | Parent only |
| `school_name`, `grade_level` | Student only |

Any other field in the body is `422 FIELD_NOT_ALLOWED`. Email is not editable.

### Error codes used here

| Code | Status | When |
|---|---|---|
| `INVALID_CREDENTIALS` | 401 | Bad login, bad refresh, or wrong password on an existing-account invite accept |
| `INVALID_OTP` | 401 | Wrong reset code, unknown email, or bad `reset_token` |
| `OTP_EXPIRED` | 410 | Reset code expired, already used, or locked |
| `ACCOUNT_DISABLED` | 403 | Password matched, `is_active` is false |
| `EMAIL_TAKEN` | 409 | `POST /auth/register` when the address already exists |
| `FIELD_NOT_ALLOWED` | 422 | Profile field that this role cannot write |
| `SUBJECT_CURRICULUM_MISMATCH` | 422 | A `subject_id` whose catalog curriculum is not allowed by `curriculum` |
| `UNAUTHENTICATED` | 401 | Missing or expired access token |

---

## Log in

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/auth/login" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Rotate refresh token

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/auth/refresh" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Log out

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/auth/logout" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Current user

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/auth/me" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Register as instructor

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/auth/register" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Request a password reset

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/auth/password/forgot" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Verify the reset OTP

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/auth/password/otp/verify" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Reset a password

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/auth/password/reset" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Get own profile

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/me/profile" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Update own profile

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/me/profile" method="patch" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## List active devices

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/me/sessions" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Revoke a device

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/me/sessions/{sessionId}" method="delete" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
