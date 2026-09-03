import '../../src/types/express.js';
import express, { type Express } from 'express';
import request from 'supertest';
import { RoleName } from '@prisma/client';
import type { AuthContext } from '../../src/types/auth.js';

const { requireRole } = await import('../../src/middleware/require-role.js');
const { errorHandler } = await import('../../src/middleware/error-handler.js');

const USER_ID = '11111111-1111-4111-8111-111111111111';
const SESSION_ID = '99999999-9999-4999-8999-999999999999';

/** A route protected by `requireRole`, with `req.auth` planted by a stub. */
const guardedApp = (allowed: RoleName[], auth?: AuthContext): Express => {
  const app = express();
  app.use((req, _res, next) => {
    if (auth !== undefined) {
      req.auth = auth;
    }
    next();
  });
  app.get('/guarded', requireRole(...allowed), (_req, res) => {
    res.status(200).json({ ok: true });
  });
  app.use(errorHandler);
  return app;
};

const authFor = (...roles: RoleName[]): AuthContext => ({
  userId: USER_ID,
  sessionId: SESSION_ID,
  roles,
});

describe('requireRole', () => {
  it('is unauthenticated, not forbidden, when no auth context was established', async () => {
    const response = await request(guardedApp([RoleName.TEACHER])).get('/guarded');

    expect(response.status).toBe(401);
    expect(response.body.error.code).toBe('UNAUTHENTICATED');
  });

  it.each([
    RoleName.TEACHER,
    RoleName.ASSISTANT,
    RoleName.PARENT,
    RoleName.STUDENT,
    RoleName.ADMIN,
  ])('admits %s when that role is on the allow list', async (role) => {
    const response = await request(guardedApp([role], authFor(role))).get('/guarded');

    expect(response.status).toBe(200);
    expect(response.body).toEqual({ ok: true });
  });

  it.each([
    [RoleName.STUDENT, [RoleName.TEACHER]],
    [RoleName.PARENT, [RoleName.TEACHER, RoleName.ASSISTANT]],
    [RoleName.TEACHER, [RoleName.ADMIN]],
    [RoleName.ASSISTANT, [RoleName.STUDENT, RoleName.PARENT]],
  ])('refuses %s when the route allows %j', async (role, allowed) => {
    const response = await request(guardedApp(allowed, authFor(role))).get('/guarded');

    expect(response.status).toBe(403);
    expect(response.body.error).toMatchObject({
      code: 'INSUFFICIENT_SCOPE',
      message: 'Insufficient role',
    });
  });

  it('admits a multi-role user when any one of their roles is allowed', async () => {
    const app = guardedApp([RoleName.TEACHER], authFor(RoleName.STUDENT, RoleName.TEACHER));

    const response = await request(app).get('/guarded');

    expect(response.status).toBe(200);
  });

  it('refuses a user whose role list is empty', async () => {
    const response = await request(guardedApp([RoleName.TEACHER], authFor())).get('/guarded');

    expect(response.status).toBe(403);
    expect(response.body.error.code).toBe('INSUFFICIENT_SCOPE');
  });

  it('refuses every role when the allow list is empty', async () => {
    const response = await request(guardedApp([], authFor(RoleName.ADMIN))).get('/guarded');

    expect(response.status).toBe(403);
  });
});
