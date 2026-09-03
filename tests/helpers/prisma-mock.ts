import { jest } from '@jest/globals';

/**
 * Importing this module registers the `src/config/database.js` mock. Test files
 * must import it *statically* — so it is evaluated first — and then reach the
 * code under test through a dynamic `await import(...)`.
 */

/** Id handed back by the default `userSession.create` stub. */
export const SESSION_ID = '99999999-9999-4999-8999-999999999999';

/** Every Prisma delegate method we touch takes one options object and resolves. */
type PrismaCall = (args?: unknown) => Promise<unknown>;

const delegate = (): jest.Mock<PrismaCall> => jest.fn<PrismaCall>();

export const prismaMock = {
  user: {
    findUnique: delegate(),
    update: delegate(),
  },
  userSession: {
    create: delegate(),
    findUnique: delegate(),
    findFirst: delegate(),
    findMany: delegate(),
    update: delegate(),
    updateMany: delegate(),
    count: delegate(),
  },
  $transaction: delegate(),
};

jest.unstable_mockModule('../../src/config/database.js', () => ({
  prisma: prismaMock,
  connectDatabase: jest.fn(),
  disconnectDatabase: jest.fn(),
  isDatabaseHealthy: jest.fn<() => Promise<boolean>>().mockResolvedValue(true),
}));

/** Neutral defaults so an unstubbed call never leaks a real query or `undefined`. */
export const resetPrismaMock = (): void => {
  prismaMock.user.findUnique.mockResolvedValue(null);
  prismaMock.user.update.mockResolvedValue({});
  prismaMock.userSession.create.mockResolvedValue({ id: SESSION_ID });
  prismaMock.userSession.findUnique.mockResolvedValue(null);
  prismaMock.userSession.findFirst.mockResolvedValue(null);
  prismaMock.userSession.findMany.mockResolvedValue([]);
  prismaMock.userSession.update.mockResolvedValue({});
  prismaMock.userSession.updateMany.mockResolvedValue({ count: 0 });
  prismaMock.userSession.count.mockResolvedValue(0);
  prismaMock.$transaction.mockResolvedValue([]);
};

/** Reads the single options object a delegate was called with. */
export const callArg = <T>(mock: jest.Mock<PrismaCall>, index = 0): T =>
  mock.mock.calls[index]?.[0] as T;
