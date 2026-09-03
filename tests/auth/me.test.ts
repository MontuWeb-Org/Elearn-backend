import request from 'supertest';
import { RoleName } from '@prisma/client';
import { prismaMock, resetPrismaMock } from '../helpers/prisma-mock.js';
import { buildSession, buildUser, rolesOf, type TestUser } from '../helpers/fixtures.js';

const { createApp } = await import('../../src/app.js');
const { signAccessToken } = await import('../../src/modules/auth/token.service.js');

const app = createApp();
const ME_URL = '/api/v1/auth/me';

const session = buildSession();

/** Wires up an authenticated request for `user` with the given token roles. */
const authorize = (user: TestUser, tokenRoles: RoleName[]): string => {
  prismaMock.userSession.findFirst.mockResolvedValue({ ...session, userId: user.id, user });
  prismaMock.user.findUnique.mockResolvedValue(user);
  return signAccessToken({ sub: user.id, sid: session.id, roles: tokenRoles, typ: 'access' });
};

beforeEach(() => {
  resetPrismaMock();
});

describe('GET /api/v1/auth/me', () => {
  it.each([
    [RoleName.TEACHER, 'instructor'],
    [RoleName.ASSISTANT, 'assistant'],
    [RoleName.PARENT, 'parent'],
    [RoleName.STUDENT, 'student'],
  ])('returns the %s profile with routing target %s', async (role, routingTarget) => {
    const user = buildUser({ roles: rolesOf(role), avatarUrl: 'https://cdn.montu.test/a.png' });
    const token = authorize(user, [role]);

    const response = await request(app).get(ME_URL).set('Authorization', `Bearer ${token}`);

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      id: user.id,
      email: user.email,
      full_name: user.fullName,
      avatar_url: 'https://cdn.montu.test/a.png',
      roles: [role],
      routing_target: routingTarget,
    });
  });

  it('never leaks the password hash', async () => {
    const user = buildUser();
    const token = authorize(user, [RoleName.TEACHER]);

    const response = await request(app).get(ME_URL).set('Authorization', `Bearer ${token}`);

    expect(response.text).not.toContain(user.passwordHash);
    expect(response.body).not.toHaveProperty('passwordHash');
    expect(response.body).not.toHaveProperty('password_hash');
  });

  it('resolves roles from the database rather than trusting the token', async () => {
    // The token was minted while the user was a STUDENT; the record now says
    // TEACHER, and the response must follow the record.
    const user = buildUser({ roles: rolesOf(RoleName.TEACHER) });
    const token = authorize(user, [RoleName.STUDENT]);

    const response = await request(app).get(ME_URL).set('Authorization', `Bearer ${token}`);

    expect(response.status).toBe(200);
    expect(response.body.roles).toEqual([RoleName.TEACHER]);
    expect(response.body.routing_target).toBe('instructor');
  });

  it('requires a token', async () => {
    const response = await request(app).get(ME_URL);

    expect(response.status).toBe(401);
    expect(response.body.error.code).toBe('UNAUTHENTICATED');
  });

  it('rejects a token that carries no roles at all', async () => {
    const user = buildUser();
    const token = authorize(user, []);

    const response = await request(app).get(ME_URL).set('Authorization', `Bearer ${token}`);

    expect(response.status).toBe(403);
    expect(response.body.error.code).toBe('INSUFFICIENT_SCOPE');
    expect(prismaMock.user.findUnique).not.toHaveBeenCalled();
  });

  it('lets an admin past the route guard but refuses to route them', async () => {
    // ADMIN is an allowed role on /me yet has no routing target, so the guard
    // passes and the profile serialiser is what rejects the request.
    const user = buildUser({ roles: rolesOf(RoleName.ADMIN) });
    const token = authorize(user, [RoleName.ADMIN]);

    const response = await request(app).get(ME_URL).set('Authorization', `Bearer ${token}`);

    expect(response.status).toBe(403);
    expect(response.body.error.code).toBe('INSUFFICIENT_SCOPE');
    expect(prismaMock.user.findUnique).toHaveBeenCalled();
  });

  it('rejects a deactivated account at the authentication step', async () => {
    const user = buildUser({ isActive: false });
    const token = authorize(user, [RoleName.TEACHER]);

    const response = await request(app).get(ME_URL).set('Authorization', `Bearer ${token}`);

    expect(response.status).toBe(403);
    expect(response.body.error.code).toBe('ACCOUNT_DISABLED');
  });

  it('rejects the request when the user record has been deleted', async () => {
    const user = buildUser();
    const token = authorize(user, [RoleName.TEACHER]);
    prismaMock.user.findUnique.mockResolvedValue(null);

    const response = await request(app).get(ME_URL).set('Authorization', `Bearer ${token}`);

    expect(response.status).toBe(403);
    expect(response.body.error.code).toBe('ACCOUNT_DISABLED');
  });
});
