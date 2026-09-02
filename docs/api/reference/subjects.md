# Subjects

Platform catalog. The frontend **never hardcodes subject names** — it loads this list, filtered by
the curriculum the user just picked.

Each row belongs to one track. Physics IGCSE and Physics American Diploma are two ids. Sign-up
sends those ids as `subject_ids`; course create sends one as `subject_id`.

{% hint style="info" %}
1 operation — **ready**. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}

## Client flow

1. User picks a curriculum chip (`IGCSE`, `American Diploma`, or `Both`).
2. `GET /subjects?curriculum=IGCSE` — or omit the query for both tracks when they chose `Both`.
3. Render the names **in array order**. Submit the `subject_id` values, never the labels. Do not send `order_index` — it is not in this response.

```http
GET /api/v1/subjects?curriculum=IGCSE
```

```json
[
  {
    "subject_id": "9f2a1c4e-...",
    "name": "Physics",
    "curriculum": "IGCSE"
  }
]
```

Public — no bearer token. Signup (WF 02) calls this before the account exists.

## List subjects

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/subjects" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
