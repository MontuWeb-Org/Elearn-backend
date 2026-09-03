import jwt from 'jsonwebtoken';
import request from 'supertest';
import { RoleName } from '@prisma/client';
import { callArg, prismaMock, resetPrismaMock } from '../helpers/prisma-mock.js';
import { buildSession, buildUser, rolesOf } from '../helpers/fixtures.js';

const { createApp } = await import('../../src/app.js');
const { sha256Hex } = await import('../../src/utils/crypto.js');

const app = createApp();
const REFRESH_URL = '/api/v1/auth/refresh';
const DAY_MS = 24 * 60 * 60 * 1000;
const PRESENTED_TOKEN = 'presented-refresh-token';

beforeEach(() => {
  resetPrismaMock();
});

describe('POST /api/v1/auth/refresh', () => {
  describe('rotation', () => {
    it('looks the session up by the hash of the presented token', async () => {
      const user = buildUser();
      prismaMock.userSession.findUnique.mockResolvedValue(buildSession({ userId: user.id }));
      prismaMock.user.findUnique.mockResolvedValue(user);

      await request(app).post(REFRESH_URL).send({ refresh_token: PRESENTED_TOKEN });

      const args = callArg<{ where: { refreshTokenHash: string } }>(
        prismaMock.userSession.findUnique,
      );
      expect(args.where.refreshTokenHash).toBe(sha256Hex(PRESENTED_TOKEN));
    });

    it('issues a new refresh token and stores its hash in place of the old one', async () => {
      const user = buildUser();
      const session = buildSession({ userId: user.id });
      prismaMock.userSession.findUnique.mockResolvedValue(session);
      prismaMock.user.findUnique.mockResolvedValue(user);

      const response = await request(app)
        .post(REFRESH_URL)
        .send({ refresh_token: PRESENTED_TOKEN });

      expect(response.status).toBe(200);
      const next = response.body.refresh_token as string;
      expect(next).toEqual(expect.any(String));
      expect(next).not.toBe(PRESENTED_TOKEN);

      const args = callArg<{ where: { id: string }; data: { refreshTokenHash: string } }>(
        prismaMock.userSession.update,
      );
      expect(args.where.id).toBe(session.id);
      expect(args.data.refreshTokenHash).toBe(sha256Hex(next));
      expect(args.data.refreshTokenHash).not.toBe(sha256Hex(PRESENTED_TOKEN));
    });

    it('mints an access token bound to the same session with freshly read roles', async () => {
      // Roles are re-read from the database on every refresh, so a role change
      // takes effect on the next rotation rather than at the next full login.
      const user = buildUser({ roles: rolesOf(RoleName.STUDENT, RoleName.PARENT) });
      const session = buildSession({ userId: user.id });
      prismaMock.userSession.findUnique.mockResolvedValue(session);
      prismaMock.user.findUnique.mockResolvedValue(user);

      const response = await request(app)
        .post(REFRESH_URL)
        .send({ refresh_token: PRESENTED_TOKEN });

      expect(response.status).toBe(200);
      const payload = jwt.verify(
        response.body.access_token,
        process.env.JWT_SECRET as string,
      ) as jwt.JwtPayload;

      expect(payload.sid).toBe(session.id);
      expect(payload.sub).toBe(user.id);
      expect(payload.roles).toEqual([RoleName.STUDENT, RoleName.PARENT]);
      expect(response.body.user.routing_target).toBe('parent');
    });

    it('keeps the remembered 30-day window across a rotation', async () => {
      const user = buildUser();
      prismaMock.userSession.findUnique.mockResolvedValue(
        buildSession({ userId: user.id, rememberMe: true }),
      );
      prismaMock.user.findUnique.mockResolvedValue(user);

      await request(app).post(REFRESH_URL).send({ refresh_token: PRESENTED_TOKEN });

      const args = callArg<{ data: { expiresAt: Date } }>(prismaMock.userSession.update);
      expect(args.data.expiresAt.getTime() - Date.now()).toBeGreaterThan(29.5 * DAY_MS);
    });
  });

  describe('rejection', () => {
    it('rejects a token that matches no session', async () => {
      prismaMock.userSession.findUnique.mockResolvedValue(null);

      const response = await request(app)
        .post(REFRESH_URL)
        .send({ refresh_token: PRESENTED_TOKEN });

      expect(response.status).toBe(401);
      expect(response.body.error.code).toBe('INVALID_CREDENTIALS');
      expect(prismaMock.userSession.update).not.toHaveBeenCalled();
    });

    it('rejects a revoked session', async () => {
      prismaMock.userSession.findUnique.mockResolvedValue(buildSession({ isRevoked: true }));

      const response = await request(app)
        .post(REFRESH_URL)
        .send({ refresh_token: PRESENTED_TOKEN });

      expect(response.status).toBe(401);
      expect(prismaMock.userSession.update).not.toHaveBeenCalled();
    });

    it('rejects an expired session', async () => {
      prismaMock.userSession.findUnique.mockResolvedValue(
        buildSession({ expiresAt: new Date(Date.now() - 1000) }),
      );

      const response = await request(app)
        .post(REFRESH_URL)
        .send({ refresh_token: PRESENTED_TOKEN });

      expect(response.status).toBe(401);
      expect(prismaMock.userSession.update).not.toHaveBeenCalled();
    });

    it('rejects a rotation for a deactivated account', async () => {
      const user = buildUser({ isActive: false });
      prismaMock.userSession.findUnique.mockResolvedValue(buildSession({ userId: user.id }));
      prismaMock.user.findUnique.mockResolvedValue(user);

      const response = await request(app)
        .post(REFRESH_URL)
        .send({ refresh_token: PRESENTED_TOKEN });

      expect(response.status).toBe(401);
      expect(response.body.error.code).toBe('INVALID_CREDENTIALS');
    });

    it('rejects a rotation when the user record has disappeared', async () => {
      prismaMock.userSession.findUnique.mockResolvedValue(buildSession());
      prismaMock.user.findUnique.mockResolvedValue(null);

      const response = await request(app)
        .post(REFRESH_URL)
        .send({ refresh_token: PRESENTED_TOKEN });

      expect(response.status).toBe(401);
    });

    it('rejects a rotation for a user left with no routable role', async () => {
      const user = buildUser({ roles: rolesOf(RoleName.ADMIN) });
      prismaMock.userSession.findUnique.mockResolvedValue(buildSession({ userId: user.id }));
      prismaMock.user.findUnique.mockResolvedValue(user);

      const response = await request(app)
        .post(REFRESH_URL)
        .send({ refresh_token: PRESENTED_TOKEN });

      expect(response.status).toBe(403);
      expect(response.body.error.code).toBe('INSUFFICIENT_SCOPE');
    });

    it.each([
      ['a missing refresh_token', {}],
      ['an empty refresh_token', { refresh_token: '' }],
      ['a non-string refresh_token', { refresh_token: 42 }],
    ])('rejects %s with 400', async (_label, body) => {
      const response = await request(app).post(REFRESH_URL).send(body);

      expect(response.status).toBe(400);
      expect(response.body.error.code).toBe('VALIDATION_ERROR');
      expect(prismaMock.userSession.findUnique).not.toHaveBeenCalled();
    });
  });
});
