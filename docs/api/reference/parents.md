# Parent portal

Parents monitor; they never edit. Two invariants govern every endpoint in this group:

1. **A parent reads nothing outside their linked children.** Every query is filtered by the caller's `PARENT_STUDENTS` rows. No parent-visible endpoint accepts a `student_id` without that check.
2. **A parent is read-only on academic records.** Attendance, grades and schedule are never writable by a parent. The single parent write in the entire API is fee payment.

The parent–child link is many-to-many in both directions: one parent follows several children, and one child may be followed by both parents. It is deliberately **not** scoped to an instructor — a parent with children under two instructors holds one account and one set of links.

{% hint style="info" %}
6 operations — **4 ready**, **1** awaiting a decision, **1 blocked**. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}


## List linked children

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/me/children" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Get a child

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/children/{studentId}" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Child attendance tab

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/children/{studentId}/attendance" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Child grades tab

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/children/{studentId}/grades" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Child schedule tab

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/children/{studentId}/schedule" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Child fees tab

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/children/{studentId}/fees" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
