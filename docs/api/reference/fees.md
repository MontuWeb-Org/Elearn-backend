# Fees

Student → instructor payments. **Distinct from [Billing](billing.md)**, which is the instructor's own subscription to the platform. Two different money flows, two different entity sets.

{% hint style="info" %}
5 operations — **5 blocked**. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}


## Revenue summary

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/fees/summary" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## List student fees

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/fees" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Send a payment reminder

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/fees/{feeId}/remind" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Get a receipt

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/fees/{feeId}/receipt" method="get" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}


## Pay a fee

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/payments" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
