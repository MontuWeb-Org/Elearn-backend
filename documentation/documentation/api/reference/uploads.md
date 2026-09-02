# Uploads

Files live in external storage; the database holds URLs only. Upload transport is deliberately separate from the resource APIs: request a signed target here, `PUT` the bytes directly to it, then pass the returned `file_url` to whichever create call needs it.

{% hint style="info" %}
1 operations — **1** awaiting a decision. Each operation states its own status; see [Specification status](../concepts/status.md) for what the labels mean.
{% endhint %}


## Request an upload target

{% openapi src="https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml" path="/uploads" method="post" %}
https://raw.githubusercontent.com/MontuWeb-Org/Elearn-backend/main/docs/api/openapi.yaml
{% endopenapi %}
