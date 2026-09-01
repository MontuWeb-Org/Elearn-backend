# Roster

Who is keeping up and who is not, across 150+ students and multiple sections. Every aggregate on these endpoints — attendance percentage, average grade, homework state — is **computed on read and never stored**.

{% hint style="info" %}
4 operations — **2 ready**, **2** awaiting a decision. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}


## List students

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/students" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Get a student

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/students/{studentId}" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Student attendance history

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/students/{studentId}/attendance" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Student grade history

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/students/{studentId}/grades" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
