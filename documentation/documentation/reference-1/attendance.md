# Attendance

Attendance records against a **live session**, never against a lesson, a course or a day.

Saving is a single bulk `PUT` carrying the full status array. That one endpoint serves both "Mark all present" and "Save Attendance" — at 150+ students, one request per student is the wrong shape.

**Instructor Session View (WF 10) and TA Attendance (WF 16) use this same API.** Same GET, same PUT, same override. The TA still needs `can_take_attendance`.

**Past-session roster** is recorded rows **union** current group members. Cancelled sessions are not in the attendance-percentage denominator.

{% hint style="info" %}
5 operations — **5 ready**. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}


## Get the attendance roster

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/live-sessions/{sessionId}/attendance" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Save attendance

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/live-sessions/{sessionId}/attendance" method="put" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Override one student

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/attendance/{attendanceId}" method="patch" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## End session and save attendance

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/live-sessions/{sessionId}/end" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Auto-mark on join

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/live-sessions/{sessionId}/attendance/self" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
