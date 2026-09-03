/**
 * Local instructor account matching the Postman "Elearn Local" environment.
 * Run with `npm run db:seed` — refuses to run in production.
 */
import { connectDatabase, disconnectDatabase, prisma } from '../src/config/database.js';
import { isProduction } from '../src/config/env.js';
import { RoleName } from '../src/models/index.js';
import { hashPassword } from '../src/modules/auth/password.service.js';
import { logger } from '../src/utils/index.js';

const EMAIL = 'you@example.com';
const PASSWORD = 'Password1!';
const FULL_NAME = 'Local Dev User';

const main = async (): Promise<void> => {
  if (isProduction) {
    logger.error('db:seed is for local development only');
    process.exit(1);
  }

  await connectDatabase();

  const passwordHash = await hashPassword(PASSWORD);
  const user = await prisma.user.upsert({
    where: { email: EMAIL },
    create: { email: EMAIL, passwordHash, fullName: FULL_NAME, isActive: true },
    update: { passwordHash, fullName: FULL_NAME, isActive: true },
  });

  const role = await prisma.role.findUnique({ where: { name: RoleName.TEACHER } });
  if (role === null) {
    throw new Error('TEACHER role is missing — run migrations first');
  }

  await prisma.userRole.upsert({
    where: { userId_roleId: { userId: user.id, roleId: role.id } },
    create: { userId: user.id, roleId: role.id },
    update: {},
  });

  logger.info(`Seeded ${EMAIL} (${PASSWORD}) as TEACHER — routing_target instructor`);
  await disconnectDatabase();
};

main().catch((error: unknown) => {
  logger.error('Seed failed', error);
  process.exit(1);
});
