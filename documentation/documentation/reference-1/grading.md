# Grading

The teaching assistant's queue, and the whole of wireframe 15.

Two facts shape every endpoint here:

**The queue is a query, not a table.** Pending work is `QUIZ_ANSWERS` where `points_awarded IS NULL`, joined to `QUIZ_QUESTIONS` on `question_type = 'STRUCTURED'` and to `GROUP_ASSISTANTS` for scope. A partial index exists for exactly this shape.

**The unit of work is one answer, not one attempt.** The queue serves "Youssef T. — Q4 (structured answer)" with its own score box. `GET /grading/queue/next` takes a soft claim so Skip does not re-serve the same essay. The claim is advisory and never blocks a grade.

MCQs never appear here — they are auto-scored at submit. A null `graded_by_user_id` on a scored answer means the machine graded it, not that attribution is missing.

**Auto-finalize.** When the TA grades the last structured question on an attempt, that attempt becomes `GRADED` and `quiz.graded` fans out. `POST .../finalize` is an instructor override only.

**Assignments have no grading queue.** They are checked for on-time submission and self-checked against a released solution. The only homework action on this screen is uploading that solution, which needs `can_upload_solutions`, not `can_grade`.

{% hint style="info" %}
8 operations — **8 ready**. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}


## Get the grading queue

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/grading/queue" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Get pending counts

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/grading/summary" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Serve the next item

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/grading/queue/next" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Skip an item

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/grading/queue/{answerId}/skip" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Grade answers in bulk

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/grading/answers" method="patch" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## List attempts for a quiz

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/quizzes/{quizId}/attempts" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Grade one answer

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/answers/{answerId}/grade" method="patch" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Finalize grading

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/attempts/{attemptId}/finalize" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
