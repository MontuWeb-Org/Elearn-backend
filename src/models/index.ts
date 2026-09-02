/**
 * Prisma generates the concrete model types; this barrel is the single place
 * the rest of the app imports them from, so call sites never reach into
 * `@prisma/client` directly.
 */
export type { Prisma, User } from '@prisma/client';
export { Role } from '@prisma/client';
