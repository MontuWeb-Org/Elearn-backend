# Elearn Backend

Backend API for the Montu Elearn platform — Node.js, Express 5, TypeScript, Prisma and PostgreSQL.

## Requirements

- Node.js >= 20 (CI runs 22)
- PostgreSQL 16 (a `docker-compose.yml` is provided for local use)

## Getting started

```bash
npm install
cp .env.example .env          # then fill in DATABASE_URL
docker compose up -d postgres mailpit # or point DATABASE_URL at your own instance
npm run db:migrate            # applies prisma/migrations
npm run db:seed               # you@example.com / Password1! (instructor)
npm run db:check              # verifies the PostgreSQL connection
npm run dev
```

The API is served under `/api/v1`. Health endpoints:

| Method | Path                   | Purpose                                       |
| ------ | ---------------------- | --------------------------------------------- |
| GET    | `/api/v1/health`       | Liveness — the process is up                  |
| GET    | `/api/v1/health/ready` | Readiness — PostgreSQL reachable (503 if not) |

## Postman

Import these two files (File → Import), then pick **Elearn Local** in the environment dropdown:

- `postman/Elearn-API.postman_collection.json` — live endpoints only
- `postman/Elearn-Local.postman_environment.json` — `baseUrl`, email, password, tokens

After `npm run db:seed`, **Elearn Local** already matches `you@example.com` / `Password1!`. Run **Auth → Login**. That request stores `access_token` so Bearer routes work.

Forgot-password OTPs go to Mailpit at http://localhost:8025 when `SMTP_HOST` is set. Development also logs the code in the API terminal.

Do not import `docs/api/openapi.yaml` into Postman — it is OpenAPI 3.1 and Postman often rejects it.

## Scripts

| Script                 | What it does                             |
| ---------------------- | ---------------------------------------- |
| `npm run dev`          | Watch-mode dev server (tsx)              |
| `npm run build`        | `prisma generate` + `tsc` into `dist/`   |
| `npm start`            | Run the compiled server from `dist/`     |
| `npm run typecheck`    | Type-check without emitting              |
| `npm run lint`         | ESLint (type-aware)                      |
| `npm run lint:fix`     | ESLint with autofix                      |
| `npm run format`       | Prettier write                           |
| `npm run format:check` | Prettier check (CI gate)                 |
| `npm run db:generate`  | Regenerate the Prisma client             |
| `npm run db:migrate`   | Create/apply a migration in development  |
| `npm run db:deploy`    | Apply pending migrations (CI/production) |
| `npm run db:studio`    | Prisma Studio                            |
| `npm run db:check`     | Standalone PostgreSQL connectivity check |
| `npm run db:seed`      | Local instructor `you@example.com` / `Password1!` |

## Project structure

```
src/
  app.ts                 Express app assembly (middleware + routes)
  server.ts              Process entry: connect DB, listen, graceful shutdown
  config/                Env, Prisma client, in-memory cache
  modules/               Feature modules (routes, controllers, services, schemas)
    auth/
    health/
  middleware/            Auth, validation, logging, 404, error handler
  models/                Barrel over Prisma-generated model types
  routes/                API aggregator — mounts feature routers under /api/v1
  types/                 Shared domain and Express types
  utils/                 Logger, HttpError, crypto, pagination, constants
scripts/                 Operational scripts (db-check, docs bootstrap)
prisma/
  schema.prisma          Data model
  migrations/            Versioned SQL migrations
```

Adding a feature usually means: `prisma/schema.prisma` → migration → a folder under
`src/modules/<feature>/`, then mount its router in `src/routes/index.ts`.

## Configuration

All variables are validated at startup by `src/config/env.ts`; the process exits with a
readable message if any are missing or malformed. See `.env.example` for the full list.

Note that Prisma 7 no longer reads `url` from `schema.prisma`: the CLI takes it from
`prisma.config.ts` and the runtime client connects through the `@prisma/adapter-pg`
driver adapter in `src/config/database.ts`. Both read the same `DATABASE_URL`.

## Connecting to Supabase

Two provider-specific gotchas, both already handled in `.env.example` and `src/config/database.ts`:

1. **Use the pooler host, not the direct one.** `db.<ref>.supabase.co` resolves to an
   IPv6 address only. Networks without IPv6 egress (WSL2, many CI runners, most home
   ISPs) fail with `connect ENETUNREACH`, and no DNS setting helps because there is no
   A record to fall back to. Use the Supavisor pooler instead — it is IPv4-reachable:

   ```
   postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```

   Port `5432` is session mode (what this project uses); `6543` is transaction mode and
   needs `?pgbouncer=true`. The exact host and user are in Dashboard → Connect.

2. **Pin the CA.** Supabase serves TLS from a private root CA that is in no public trust
   store, so verification fails with `self-signed certificate in certificate chain`. The
   root is committed at `certs/supabase-prod-ca-2021.crt`; point `DATABASE_CA_CERT` at it.
   It is a public certificate, not a secret.

   Note that `sslmode` must **not** appear in `DATABASE_URL` when pinning a CA:
   node-postgres builds its TLS options from `sslmode` and then ignores the `ssl` config
   entirely, silently discarding the CA. `src/config/database.ts` strips it defensively.
   Certificate verification stays enabled throughout — the fix is to trust the right
   root, never to skip the check.

## CI

`.github/workflows/ci.yml` runs on every PR to `main` (and on push to `main`) with three jobs:

- **quality** — lint, Prettier check, typecheck
- **build** — `npm run build`, uploads `dist/` as an artifact
- **database** — starts a `postgres:16` service, applies migrations, runs the connectivity check
# docs

