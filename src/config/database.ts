import { readFileSync } from 'node:fs';
import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from '@prisma/client';
import { env, isProduction } from './env.js';
import { logger } from '../utils/logger.js';

/**
 * Some managed providers (Supabase among them) serve TLS from a private root CA
 * that is in no public trust store, so the chain must be pinned explicitly.
 * Verification stays enabled — we never fall back to trusting blindly.
 */
const buildConnectionConfig = (): {
  connectionString: string;
  ssl?: { ca: string; rejectUnauthorized: true };
} => {
  if (env.DATABASE_CA_CERT === undefined) {
    return { connectionString: env.DATABASE_URL };
  }

  // node-postgres builds its own TLS options from `sslmode` and then ignores the
  // `ssl` config entirely, which would silently discard the CA we just pinned.
  // Strip the parameter so TLS is driven only from here. Done textually rather
  // than via `new URL()` so credentials in the string are never re-encoded.
  const connectionString = env.DATABASE_URL.replace(/([?&])sslmode=[^&]*/gi, '$1')
    .replace(/\?&/, '?')
    .replace(/&&+/g, '&')
    .replace(/[?&]$/, '');

  return {
    connectionString,
    ssl: { ca: readFileSync(env.DATABASE_CA_CERT, 'utf8'), rejectUnauthorized: true },
  };
};

// Prisma 7 connects through a driver adapter rather than a `url` in the schema.
const createPrismaClient = (): PrismaClient =>
  new PrismaClient({
    adapter: new PrismaPg(buildConnectionConfig()),
    log: isProduction ? ['error'] : ['warn', 'error'],
  });

// Reuse one client across hot reloads in development so we don't exhaust the
// PostgreSQL connection pool.
const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient };

export const prisma: PrismaClient = globalForPrisma.prisma ?? createPrismaClient();

if (!isProduction) {
  globalForPrisma.prisma = prisma;
}

/** Opens the connection eagerly so startup fails fast on a bad DATABASE_URL. */
export const connectDatabase = async (): Promise<void> => {
  await prisma.$connect();
  const [row] = await prisma.$queryRaw<[{ version: string }]>`SELECT version()`;
  logger.info(`PostgreSQL connected (${env.NODE_ENV})`, row?.version.split(',')[0]);
};

export const disconnectDatabase = async (): Promise<void> => {
  await prisma.$disconnect();
  logger.info('PostgreSQL disconnected');
};

/** Cheap liveness probe used by the health endpoint. */
export const isDatabaseHealthy = async (): Promise<boolean> => {
  try {
    await prisma.$queryRaw`SELECT 1`;
    return true;
  } catch (error) {
    logger.error('Database health check failed', error);
    return false;
  }
};
