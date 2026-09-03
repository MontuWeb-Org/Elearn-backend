import '../types/express.js';
import type { RequestHandler } from 'express';
import { findActiveSession } from '../modules/auth/session.service.js';
import { verifyAccessToken } from '../modules/auth/token.service.js';
import { asyncHandler, HttpError } from '../utils/index.js';

const bearerPrefix = 'Bearer ';

export const requireAuth: RequestHandler = asyncHandler(async (req, _res, next) => {
  const header = req.headers.authorization;
  if (header === undefined || !header.startsWith(bearerPrefix)) {
    throw HttpError.unauthorized('Missing token', 'UNAUTHENTICATED');
  }

  const payload = verifyAccessToken(header.slice(bearerPrefix.length));
  const session = await findActiveSession(payload.sid);

  if (session === null || session.userId !== payload.sub) {
    throw HttpError.unauthorized('Invalid token', 'UNAUTHENTICATED');
  }

  if (!session.user.isActive) {
    throw HttpError.forbidden('Account disabled', 'ACCOUNT_DISABLED');
  }

  req.auth = {
    userId: payload.sub,
    sessionId: payload.sid,
    roles: payload.roles,
  };
  next();
});
