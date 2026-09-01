# Quizzes

Timed assessments on the **cohort branch**: issued to one group, with an availability window and a per-attempt clock.

`opens_at` and `closes_at` bound when the quiz is available; `duration_seconds` is the clock that starts when a student begins. A quiz may be open for a week but allow 30 minutes once started — either bound may bind first. Omit the duration for an untimed quiz.

`lesson_id` on a quiz is **tagging only**. It does not move the quiz onto the curriculum branch, and it must belong to the group's own course.

{% hint style="info" %}
10 operations — **8 ready**, **2** awaiting a decision. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}


## List quizzes

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/quizzes" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Create a quiz

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/groups/{groupId}/quizzes" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Get a quiz

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/quizzes/{quizId}" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Update a quiz

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/quizzes/{quizId}" method="patch" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Delete a quiz

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/quizzes/{quizId}" method="delete" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## List questions

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/quizzes/{quizId}/questions" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Add a question

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/quizzes/{quizId}/questions" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Update a question

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/questions/{questionId}" method="patch" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Delete a question

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/questions/{questionId}" method="delete" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Reorder questions

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/quizzes/{quizId}/questions/order" method="put" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
