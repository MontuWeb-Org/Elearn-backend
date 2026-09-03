# Publishing & sync

How a change to the API documentation reaches the published site.

## Two things sync separately

| What | Source | Syncs by |
|---|---|---|
| Prose pages — concepts, per-resource intros, navigation | `docs/api/**/*.md` | **Git Sync**, on push to `main` |
| The API reference blocks | `docs/api/openapi.yaml` | **The GitBook CLI**, on publish |

Markdown is handled for you: push and GitBook rebuilds. The spec is separate, because GitBook keeps
its own copy of it.

{% hint style="warning" %}
A spec added by **URL** is only re-fetched every six hours. Publishing through the CLI updates it in
seconds, so the CLI is the path used here.
{% endhint %}

## One-time setup

1. Create an API token at [app.gitbook.com/account/developer](https://app.gitbook.com/account/developer).
   The GitBook user who owns the token must be an org member with **edit** (or **admin**) — a
   viewer/guest token authenticates but publish returns `403 You must have edit permission`.
2. Copy the **organization id** from any GitBook URL. It is the segment after `/o/`:

   `https://app.gitbook.com/o/`**`DaDQkGCM7r2TghFSBFLQ`**`/s/...`

   (The CLI no longer has `openapi organizations list`.)

3. Put both in `.env` (already gitignored):

   ```bash
   GITBOOK_TOKEN=gb_api_...
   GITBOOK_ORGANIZATION_ID=...
   GITBOOK_SPEC_NAME=montu-api
   ```

4. Add the same values to GitHub — `GITBOOK_TOKEN` as a **secret**, the other two as
   **variables** — under *Settings → Secrets and variables → Actions*.

## The loop

Edit the spec, check it, publish:

```bash
vim docs/api/openapi.yaml
npm run docs:lint      # catches structural errors before they ship
npm run docs:publish   # live in seconds
```

`docs:lint` is worth running every time. **A malformed spec publishes successfully and then renders
empty API blocks with no error message**, so a lint failure is much easier to diagnose than a blank
page.

## Automatic publishing

`.github/workflows/gitbook-openapi.yml` runs the same two steps on every push to `main` that
touches `openapi.yaml`. Lint failures block the publish. The workflow can also be triggered by hand
from the Actions tab.

Day to day you do not need `npm run docs:publish` — push and the workflow handles it. Use the manual
command when you want to see a change immediately without a commit.

## Editing the spec

`openapi.yaml` is hand-maintained. Adding an endpoint means three things:

1. Add the operation under `paths:` with a `tags`, `operationId`, `summary` and `description`. The
   description should carry the role line, the ownership scope, the wireframe reference and the
   status — see any existing operation for the shape.
2. Add or reuse a schema under `components/schemas`.
3. Add an OpenAPI block (`/openapi` in the editor, or copy the block from a neighbouring page) to the matching page in `reference/`, so the endpoint appears in the docs.

Step 3 is easy to forget; nothing fails if you skip it, the endpoint is simply invisible.

{% hint style="info" %}
`scripts/bootstrap-openapi.py` generated the first version of this spec from the resource map. It is
kept for reference only — **re-running it overwrites every hand edit.**
{% endhint %}
