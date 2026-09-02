/**
 * Standalone PostgreSQL connectivity check.
 * Run with `npm run db:check` — exits 0 when the database answers, 1 otherwise.
 */
import { connectDatabase, disconnectDatabase, prisma } from '../config/database.js';
import { logger } from '../utils/logger.js';

const main = async (): Promise<void> => {
  await connectDatabase();

  const [row] = await prisma.$queryRaw<
    [{ database: string; user: string }]
  >`SELECT current_database() AS database, current_user AS user`;
  logger.info(`Connected to "${row.database}" as "${row.user}"`);

  const userCount = await prisma.user.count();
  logger.info(`users table reachable, ${userCount} row(s)`);

  await disconnectDatabase();
};

main().catch((error: unknown) => {
  logger.error('Database check failed', error);
  process.exit(1);
});
