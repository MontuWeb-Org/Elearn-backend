import jwt from 'jsonwebtoken';
import request from 'supertest';
import { callArg, prismaMock, resetPrismaMock } from '../helpers/prisma-mock.js';
import { buildSession, buildUser } from '../helpers/fixtures.js';

const { createApp } = await import('../../src/app.js');
const { signAccessToken } = await import('../../src/modules/auth/token.service.js');

const app = createApp();
const LOGOUT_URL = '/api/v1/auth/logout';

const user = buildUser();
const session = buildSession({ userId: user.id });

/** Marks the session in `requireAuth`'s lookup as live and owned by `user`. */
const sessionIsLive = (overrides: { isActive?: boolean } = {}): void => {
  prismaMock.userSession.findFirst.mockResolvedValue({
    ...session,
    user: { ...user, isActive: overrides.isActive ?? true },
  });
};

const validToken = (): string =>
  signAccessToken({ sub: user.id, sid: session.id, roles: [], typ: 'access' });

beforeEach(() => {
  resetPrismaMock();
});

describe('POST /api/v1/auth/logout', () => {
  it('revokes the session named by the token and returns 204 with no body', async () => {
    sessionIsLive();
    prismaMock.userSession.updateMany.mockResolvedValue({ count: 1 });

    const response = await request(app)
      .post(LOGOUT_URL)
      .set('Authorization', `Bearer ${validToken()}`);

    expect(response.status).toBe(204);
    expect(response.text).toBe('');

    const args = callArg<{ where: { id: string; isRevoked: boolean }; data: unknown }>(
      prismaMock.userSession.updateMany,
    );
    expect(args).toEqual({
      where: { id: session.id, isRevoked: false },
      data: { isRevoked: true },
    });
  });

  it('is idempotent when the session is already revoked', async () => {
    sessionIsLive();
    prismaMock.userSession.updateMany.mockResolvedValue({ count: 0 });

    const response = await request(app)
      .post(LOGOUT_URL)
      .set('Authorization', `Bearer ${validToken()}`);

    expect(response.status).toBe(204);
  });

  describe('bearer token handling', () => {
    it('rejects a request with no Authorization header', async () => {
      const response = await request(app).post(LOGOUT_URL);

      expect(response.status).toBe(401);
      expect(response.body.error.code).toBe('UNAUTHENTICATED');
      expect(prismaMock.userSession.findFirst).not.toHaveBeenCalled();
    });

    it.each([
      ['a non-Bearer scheme', `Basic ${Buffer.from('a:b').toString('base64')}`],
      ['a lower-case bearer prefix', `bearer ${'x'.repeat(20)}`],
      ['an empty bearer value', 'Bearer '],
      ['a structurally invalid token', 'Bearer not.a.jwt'],
    ])('rejects %s', async (_label, header) => {
      const response = await request(app).post(LOGOUT_URL).set('Authorization', header);

      expect(response.status).toBe(401);
      expect(response.body.error.code).toBe('UNAUTHENTICATED');
    });

    it('rejects a token signed with a different secret', async () => {
      const forged = jwt.sign(
        { sub: user.id, sid: session.id, roles: [], typ: 'access' },
        'a-different-secret-that-is-also-long-enough',
        { algorithm: 'HS256', expiresIn: 900 },
      );

      const response = await request(app).post(LOGOUT_URL).set('Authorization', `Bearer ${forged}`);

      expect(response.status).toBe(401);
    });

    it('rejects an expired token', async () => {
      const expired = jwt.sign(
        { sub: user.id, sid: session.id, roles: [], typ: 'access' },
        process.env.JWT_SECRET as string,
        { algorithm: 'HS256', expiresIn: -60 },
      );

      const response = await request(app)
        .post(LOGOUT_URL)
        .set('Authorization', `Bearer ${expired}`);

      expect(response.status).toBe(401);
    });

    it('rejects a token whose alg is none', async () => {
      const unsigned = jwt.sign({ sub: user.id, sid: session.id, roles: [], typ: 'access' }, '', {
        algorithm: 'none',
      });

      const response = await request(app)
        .post(LOGOUT_URL)
        .set('Authorization', `Bearer ${unsigned}`);

      expect(response.status).toBe(401);
    });

    it('rejects a well-signed token that is not an access token', async () => {
      const wrongType = jwt.sign(
        { sub: user.id, sid: session.id, roles: [], typ: 'refresh' },
        process.env.JWT_SECRET as string,
        { algorithm: 'HS256', expiresIn: 900 },
      );

      const response = await request(app)
        .post(LOGOUT_URL)
        .set('Authorization', `Bearer ${wrongType}`);

      expect(response.status).toBe(401);
      expect(prismaMock.userSession.findFirst).not.toHaveBeenCalled();
    });

    it('rejects a token carrying a role that is not in the enum', async () => {
      const bogusRole = jwt.sign(
        { sub: user.id, sid: session.id, roles: ['SUPERUSER'], typ: 'access' },
        process.env.JWT_SECRET as string,
        { algorithm: 'HS256', expiresIn: 900 },
      );

      const response = await request(app)
        .post(LOGOUT_URL)
        .set('Authorization', `Bearer ${bogusRole}`);

      expect(response.status).toBe(401);
    });
  });

  describe('session state', () => {
    it('rejects a token whose session is revoked or expired', async () => {
      // `findActiveSession` filters on isRevoked/expiresAt, so a dead session
      // simply does not come back.
      prismaMock.userSession.findFirst.mockResolvedValue(null);

      const response = await request(app)
        .post(LOGOUT_URL)
        .set('Authorization', `Bearer ${validToken()}`);

      expect(response.status).toBe(401);
      expect(response.body.error.code).toBe('UNAUTHENTICATED');
      expect(prismaMock.userSession.updateMany).not.toHaveBeenCalled();
    });

    it('rejects a token whose subject does not own the session', async () => {
      prismaMock.userSession.findFirst.mockResolvedValue({
        ...session,
        userId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        user: { ...user, id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa' },
      });

      const response = await request(app)
        .post(LOGOUT_URL)
        .set('Authorization', `Bearer ${validToken()}`);

      expect(response.status).toBe(401);
      expect(prismaMock.userSession.updateMany).not.toHaveBeenCalled();
    });

    it('rejects a live session belonging to a deactivated account', async () => {
      sessionIsLive({ isActive: false });

      const response = await request(app)
        .post(LOGOUT_URL)
        .set('Authorization', `Bearer ${validToken()}`);

      expect(response.status).toBe(403);
      expect(response.body.error.code).toBe('ACCOUNT_DISABLED');
    });
  });
});
