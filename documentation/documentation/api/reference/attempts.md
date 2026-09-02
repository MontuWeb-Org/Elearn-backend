# Quiz attempts

The student side. An attempt *is* the record — there is no separate submission entity.

Starting an attempt materializes `expires_at` as `min(started_at + duration, quiz.closes_at)`. Storing it rather than recomputing it on every read is deliberate: the countdown, the auto-submit and late-answer rejection then all read one authoritative instant instead of three computations that can disagree.

On submit, MCQs auto-score into `auto_score` immediately; `total_score` stays null until a human has graded every structured answer. That split is what makes "MCQ score shows immediately, overall grade stays pending" representable.

{% hint style="info" %}
5 operations — **4 ready**, **1** awaiting a decision. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}


## Start an attempt

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/quizzes/{quizId}/attempts" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Resume an attempt

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/attempts/{attemptId}" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Autosave answers

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/attempts/{attemptId}/answers" method="patch" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Submit an attempt

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/attempts/{attemptId}/submit" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Get the result

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/attempts/{attemptId}/result" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
