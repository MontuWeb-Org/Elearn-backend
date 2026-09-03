import type { RequestHandler } from 'express';
import type { RoleName } from '../models/index.js';
import { HttpError } from '../utils/index.js';

export const requireRole =
  (...allowed: RoleName[]): RequestHandler =>
  (req, _res, next) => {
    const roles = req.auth?.roles;
    if (roles === undefined) {
      next(HttpError.unauthorized('Missing token', 'UNAUTHENTICATED'));
      return;
    }

    if (!roles.some((role) => allowed.includes(role))) {
      next(HttpError.forbidden('Insufficient role', 'INSUFFICIENT_SCOPE'));
      return;
    }

    next();
  };
