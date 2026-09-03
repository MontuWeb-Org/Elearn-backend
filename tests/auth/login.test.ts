import request from 'supertest';
import jwt from 'jsonwebtoken';
import { RoleName } from '@prisma/client';
import { callArg, prismaMock, resetPrismaMock, SESSION_ID } from '../helpers/prisma-mock.js';
import { buildUser, rolesOf, TEST_PASSWORD } from '../helpers/fixtures.js';

// The mock is registered while `prisma-mock.ts` is evaluated above, so every
// module that closes over `prisma` has to be pulled in dynamically after it.
const { createApp } = await import('../../src/app.js');
const { sha256Hex } = await import('../../src/utils/crypto.js');
const { ACCESS_TOKEN_TTL_SECONDS } = await import('../../src/utils/constants.js');

const app = createApp();
const LOGIN_URL = '/api/v1/auth/login';
const DAY_MS = 24 * 60 * 60 * 1000;

interface SessionCreateArgs {
  data: {
    userId: string;
    refreshTokenHash: string;
    rememberMe: boolean;
    expiresAt: Date;
    userAgent?: string;
    ipAddress?: string;
  };
}

beforeEach(() => {
  resetPrismaMock();
});

describe('POST /api/v1/auth/login', () => {
  describe('single entry point for every user tier', () => {
    const tiers = [
      { role: RoleName.TEACHER, routingTarget: 'instructor' },
      { role: RoleName.ASSISTANT, routingTarget: 'assistant' },
      { role: RoleName.PARENT, routingTarget: 'parent' },
      { role: RoleName.STUDENT, routingTarget: 'student' },
    ];

    it.each(tiers)(
      'resolves $role server-side and routes to $routingTarget',
      async ({ role, routingTarget }) => {
        const user = buildUser({ roles: rolesOf(role) });
        prismaMock.user.findUnique.mockResolvedValue(user);

        const response = await request(app)
          .post(LOGIN_URL)
          .send({ email: user.email, password: TEST_PASSWORD });

        expect(response.status).toBe(200);
        expect(response.body.user).toEqual({
          id: user.id,
          email: user.email,
          full_name: user.fullName,
          avatar_url: null,
          roles: [role],
          routing_target: routingTarget,
        });
      },
    );

    it('keeps the highest-priority routing target when a user holds several roles', async () => {
      // TEACHER outranks STUDENT in the routing table.
      const user = buildUser({ roles: rolesOf(RoleName.STUDENT, RoleName.TEACHER) });
      prismaMock.user.findUnique.mockResolvedValue(user);

      const response = await request(app)
        .post(LOGIN_URL)
        .send({ email: user.email, password: TEST_PASSWORD });

      expect(response.status).toBe(200);
      expect(response.body.user.roles).toEqual([RoleName.STUDENT, RoleName.TEACHER]);
      expect(response.body.user.routing_target).toBe('instructor');
    });

    it('rejects a user whose roles carry no routable target', async () => {
      const user = buildUser({ roles: rolesOf(RoleName.ADMIN) });
      prismaMock.user.findUnique.mockResolvedValue(user);

      const response = await request(app)
        .post(LOGIN_URL)
        .send({ email: user.email, password: TEST_PASSWORD });

      expect(response.status).toBe(403);
      expect(response.body.error.code).toBe('INSUFFICIENT_SCOPE');
      expect(prismaMock.userSession.create).not.toHaveBeenCalled();
    });
  });

  describe('token issuance', () => {
    it('returns a signed access token carrying the subject, session and roles', async () => {
      const user = buildUser({ roles: rolesOf(RoleName.TEACHER) });
      prismaMock.user.findUnique.mockResolvedValue(user);

      const response = await request(app)
        .post(LOGIN_URL)
        .send({ email: user.email, password: TEST_PASSWORD });

      expect(response.status).toBe(200);
      expect(response.body.expires_in).toBe(ACCESS_TOKEN_TTL_SECONDS);

      const payload = jwt.verify(response.body.access_token, process.env.JWT_SECRET as string, {
        algorithms: ['HS256'],
      }) as jwt.JwtPayload;

      expect(payload.sub).toBe(user.id);
      expect(payload.sid).toBe(SESSION_ID);
      expect(payload.roles).toEqual([RoleName.TEACHER]);
      expect(payload.typ).toBe('access');
      expect(payload.exp).toBeDefined();
    });

    it('persists only a hash of the refresh token, never the token itself', async () => {
      const user = buildUser();
      prismaMock.user.findUnique.mockResolvedValue(user);

      const response = await request(app)
        .post(LOGIN_URL)
        .send({ email: user.email, password: TEST_PASSWORD });

      const refreshToken = response.body.refresh_token as string;
      expect(refreshToken).toEqual(expect.any(String));

      const args = callArg<SessionCreateArgs>(prismaMock.userSession.create);
      expect(args.data.refreshTokenHash).toBe(sha256Hex(refreshToken));
      expect(args.data.refreshTokenHash).not.toBe(refreshToken);
      expect(args.data.userId).toBe(user.id);
    });

    it('records the client user agent and IP on the session', async () => {
      const user = buildUser();
      prismaMock.user.findUnique.mockResolvedValue(user);

      await request(app)
        .post(LOGIN_URL)
        .set('User-Agent', 'MontuTestAgent/1.0')
        .set('X-Forwarded-For', '203.0.113.7, 70.41.3.18')
        .send({ email: user.email, password: TEST_PASSWORD });

      const args = callArg<SessionCreateArgs>(prismaMock.userSession.create);
      expect(args.data.userAgent).toBe('MontuTestAgent/1.0');
      expect(args.data.ipAddress).toBe('203.0.113.7');
    });

    it('defaults remember_me to false and issues a 7-day refresh window', async () => {
      const user = buildUser();
      prismaMock.user.findUnique.mockResolvedValue(user);

      await request(app).post(LOGIN_URL).send({ email: user.email, password: TEST_PASSWORD });

      const args = callArg<SessionCreateArgs>(prismaMock.userSession.create);
      expect(args.data.rememberMe).toBe(false);
      expect(args.data.expiresAt.getTime() - Date.now()).toBeGreaterThan(6.5 * DAY_MS);
      expect(args.data.expiresAt.getTime() - Date.now()).toBeLessThan(7.5 * DAY_MS);
    });

    it('extends the refresh window to 30 days when remember_me is set', async () => {
      const user = buildUser();
      prismaMock.user.findUnique.mockResolvedValue(user);

      await request(app)
        .post(LOGIN_URL)
        .send({ email: user.email, password: TEST_PASSWORD, remember_me: true });

      const args = callArg<SessionCreateArgs>(prismaMock.userSession.create);
      expect(args.data.rememberMe).toBe(true);
      expect(args.data.expiresAt.getTime() - Date.now()).toBeGreaterThan(29.5 * DAY_MS);
      expect(args.data.expiresAt.getTime() - Date.now()).toBeLessThan(30.5 * DAY_MS);
    });

    it('stamps last_login_at on success', async () => {
      const user = buildUser();
      prismaMock.user.findUnique.mockResolvedValue(user);

      await request(app).post(LOGIN_URL).send({ email: user.email, password: TEST_PASSWORD });

      const args = callArg<{ where: { id: string }; data: { lastLoginAt: Date } }>(
        prismaMock.user.update,
      );
      expect(args.where.id).toBe(user.id);
      expect(args.data.lastLoginAt).toBeInstanceOf(Date);
    });
  });

  describe('credential rejection', () => {
    it('rejects an unknown email without revealing that it is unknown', async () => {
      prismaMock.user.findUnique.mockResolvedValue(null);

      const response = await request(app)
        .post(LOGIN_URL)
        .send({ email: 'nobody@montu.test', password: TEST_PASSWORD });

      expect(response.status).toBe(401);
      expect(response.body.error).toMatchObject({
        code: 'INVALID_CREDENTIALS',
        message: 'Invalid credentials',
      });
      expect(prismaMock.userSession.create).not.toHaveBeenCalled();
    });

    it('rejects a wrong password with the same response as an unknown email', async () => {
      const user = buildUser();
      prismaMock.user.findUnique.mockResolvedValue(user);

      const response = await request(app)
        .post(LOGIN_URL)
        .send({ email: user.email, password: 'not-the-password' });

      expect(response.status).toBe(401);
      expect(response.body.error).toMatchObject({
        code: 'INVALID_CREDENTIALS',
        message: 'Invalid credentials',
      });
      expect(prismaMock.user.update).not.toHaveBeenCalled();
      expect(prismaMock.userSession.create).not.toHaveBeenCalled();
    });

    it('never returns a token for a deactivated account', async () => {
      const user = buildUser({ isActive: false });
      prismaMock.user.findUnique.mockResolvedValue(user);

      const response = await request(app)
        .post(LOGIN_URL)
        .send({ email: user.email, password: TEST_PASSWORD });

      expect(response.status).toBe(403);
      expect(response.body.error.code).toBe('ACCOUNT_DISABLED');
      expect(response.body.access_token).toBeUndefined();
      expect(prismaMock.userSession.create).not.toHaveBeenCalled();
    });
  });

  describe('request validation', () => {
    it('trims and lower-cases the email before the lookup', async () => {
      const user = buildUser();
      prismaMock.user.findUnique.mockResolvedValue(user);

      await request(app)
        .post(LOGIN_URL)
        .send({ email: '  TEACHER@Montu.TEST  ', password: TEST_PASSWORD });

      const args = callArg<{ where: { email: string } }>(prismaMock.user.findUnique);
      expect(args.where.email).toBe('teacher@montu.test');
    });

    it.each([
      ['a malformed email', { email: 'not-an-email', password: TEST_PASSWORD }, 'email'],
      ['a missing email', { password: TEST_PASSWORD }, 'email'],
      ['a missing password', { email: 'teacher@montu.test' }, 'password'],
      ['an empty password', { email: 'teacher@montu.test', password: '' }, 'password'],
    ])('rejects %s with 400 and field details', async (_label, body, field) => {
      const response = await request(app).post(LOGIN_URL).send(body);

      expect(response.status).toBe(400);
      expect(response.body.error.code).toBe('VALIDATION_ERROR');
      expect(response.body.error.details).toEqual(
        expect.arrayContaining([expect.objectContaining({ field })]),
      );
      expect(prismaMock.user.findUnique).not.toHaveBeenCalled();
    });

    it('rejects a non-boolean remember_me', async () => {
      const response = await request(app)
        .post(LOGIN_URL)
        .send({ email: 'teacher@montu.test', password: TEST_PASSWORD, remember_me: 'yes' });

      expect(response.status).toBe(400);
      expect(response.body.error.code).toBe('VALIDATION_ERROR');
    });
  });
});
