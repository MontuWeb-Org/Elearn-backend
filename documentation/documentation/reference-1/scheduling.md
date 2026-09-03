# Scheduling

One calendar for physical center classes and virtual sessions alike. A live session is one scheduled class with its own time and room, and it is the **only** thing attendance records against.

`mode` drives two validation rules: `ONLINE` requires a `meeting_url`, `ONSITE` requires a `classroom_location`. `lesson_id` is nullable on purpose — revision, exam prep and open Q&A are real classes that map to no single lesson.

**Meeting URL is pasted, not OAuth.** The instructor copies a Zoom or Meet link into `meeting_url`. The platform does not log into Zoom/Meet, does not create the meeting, and does not receive a join log. `meeting_provider` and `external_meeting_id` exist for a later connection; until credentials exist, [the webhook](#meeting-provider-webhook) is unused and online attendance is self-mark plus the instructor/TA roster.

**Recurring edit — "this and following".** A weekly series is one `SESSION_SERIES` plus many `LIVE_SESSIONS` rows (e.g. twelve Sundays). Editing Sunday 12 with `scope=this_and_following` means "change this Sunday and every later Sunday in the series." If Sunday 15 already happened and has attendance, rewriting its time would make the roster claim students were present at a time that never occurred. **Those rows are skipped** (left unchanged) and listed in `skipped_session_ids`. Rows with no attendance are updated. `scope=this` changes only the row you opened and detaches it from the series.

**Cancelled sessions** are dropped from attendance %. `POST .../cancel` stays even though WF 09 has no cancel control.

{% hint style="info" %}
7 operations — **6 ready**, **1** awaiting a decision (the webhook, unused until a provider is connected). Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}


## List sessions

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/live-sessions" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Schedule a session

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/live-sessions" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Get a session

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/live-sessions/{sessionId}" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Update a session

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/live-sessions/{sessionId}" method="patch" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Cancel a session

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/live-sessions/{sessionId}/cancel" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Get join information

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/live-sessions/{sessionId}/join" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Meeting provider webhook

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/webhooks/meetings/{provider}" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
