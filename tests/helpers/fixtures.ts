import bcrypt from 'bcrypt';
import { RoleName } from '@prisma/client';

export const TEST_PASSWORD = 'CorrectHorse!23';

/**
 * One real bcrypt hash, generated once per test file. Cost 10 (the lowest the
 * env schema allows) keeps `verifyPassword` honest without dominating runtime.
 */
export const passwordHash: string = bcrypt.hashSync(TEST_PASSWORD, 10);

export interface TestUser {
  id: string;
  email: string;
  passwordHash: string;
  fullName: string;
  avatarUrl: string | null;
  isActive: boolean;
  dateJoined: Date;
  lastLoginAt: Date | null;
  roles: { role: { name: RoleName } }[];
}

const USER_IDS: Record<RoleName, string> = {
  [RoleName.TEACHER]: '11111111-1111-4111-8111-111111111111',
  [RoleName.ASSISTANT]: '22222222-2222-4222-8222-222222222222',
  [RoleName.PARENT]: '33333333-3333-4333-8333-333333333333',
  [RoleName.STUDENT]: '44444444-4444-4444-8444-444444444444',
  [RoleName.ADMIN]: '55555555-5555-4555-8555-555555555555',
};

export const buildUser = (overrides: Partial<TestUser> = {}): TestUser => {
  const roles = overrides.roles ?? [{ role: { name: RoleName.TEACHER } }];
  const primary = roles[0]?.role.name ?? RoleName.TEACHER;

  return {
    id: USER_IDS[primary],
    email: `${primary.toLowerCase()}@montu.test`,
    passwordHash,
    fullName: `Test ${primary}`,
    avatarUrl: null,
    isActive: true,
    dateJoined: new Date('2026-01-01T00:00:00.000Z'),
    lastLoginAt: null,
    ...overrides,
    roles,
  };
};

export const rolesOf = (...names: RoleName[]): { role: { name: RoleName } }[] =>
  names.map((name) => ({ role: { name } }));

/** A `user_sessions` row as `findUnique`/`findFirst` would return it. */
export const buildSession = (
  overrides: Partial<{
    id: string;
    userId: string;
    refreshTokenHash: string;
    userAgent: string | null;
    ipAddress: string | null;
    rememberMe: boolean;
    isRevoked: boolean;
    expiresAt: Date;
    createdAt: Date;
  }> = {},
) => ({
  id: '99999999-9999-4999-8999-999999999999',
  userId: USER_IDS[RoleName.TEACHER],
  refreshTokenHash: 'unused-hash',
  userAgent: 'jest',
  ipAddress: '127.0.0.1',
  rememberMe: false,
  isRevoked: false,
  expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
  createdAt: new Date('2026-01-01T00:00:00.000Z'),
  ...overrides,
});
