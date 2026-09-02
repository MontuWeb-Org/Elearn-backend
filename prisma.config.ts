import 'dotenv/config';
import { defineConfig, env } from 'prisma/config';

/**
 * Prisma 7 moves the datasource URL out of schema.prisma and into this file.
 * The runtime client gets its connection through the pg driver adapter in
 * src/config/database.ts; this config is what the CLI (migrate, studio) uses.
 */
export default defineConfig({
  schema: 'prisma/schema.prisma',
  migrations: {
    path: 'prisma/migrations',
  },
  datasource: {
    url: env('DATABASE_URL'),
  },
});
