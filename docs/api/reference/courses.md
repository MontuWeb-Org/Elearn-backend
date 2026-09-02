# Courses

The root of the curriculum branch. A course belongs to one instructor and fans out two ways: into chapters and lessons (the syllabus, authored once) and into groups (the sections that actually take it). See [The two branches](../concepts/two-branches.md).

`subject_id` is a catalog id from [Subjects](subjects.md). `subject_name` is joined on read from `SUBJECTS.name` — do not send it on create.

**Term is not an entity.** `title` is the WF 07 header (typically "Term 1"). A second term is a second course with the same subject.

Retire a live course with `PATCH` `status = ARCHIVED`. `DELETE` is only for an empty draft (no groups).

{% hint style="info" %}
5 operations — **all ready**. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}


## List courses

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/courses" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Create a course

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/courses" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Get a course

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/courses/{courseId}" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Update a course

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/courses/{courseId}" method="patch" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Delete a course

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/courses/{courseId}" method="delete" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
