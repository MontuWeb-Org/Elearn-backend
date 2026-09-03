/**
 * Runs before any module under test is imported, so `src/config/env.ts` sees a
 * complete, deterministic configuration. `DOTENV_CONFIG_PATH` redirects
 * `dotenv/config` at an empty file to keep a developer's local `.env` out of the
 * run.
 */
import { fileURLToPath } from 'node:url';

process.env.DOTENV_CONFIG_PATH = fileURLToPath(new URL('./.env.test', import.meta.url));
process.env.DOTENV_CONFIG_QUIET = 'true';

process.env.NODE_ENV = 'test';
process.env.LOG_LEVEL = 'error';
process.env.CORS_ORIGIN = '*';
process.env.DATABASE_URL = 'postgresql://test:test@127.0.0.1:5432/elearn_test';
process.env.JWT_SECRET = 'test-jwt-secret-value-that-is-long-enough-32';
// Lowest round count the schema allows — real bcrypt, but fast enough for CI.
process.env.BCRYPT_ROUNDS = '10';

delete process.env.DATABASE_CA_CERT;
delete process.env.SMTP_HOST;
delete process.env.SMTP_USER;
delete process.env.SMTP_PASS;
