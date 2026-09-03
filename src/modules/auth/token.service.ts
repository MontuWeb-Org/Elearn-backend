import jwt from 'jsonwebtoken';
import { env } from '../../config/env.js';
import { RoleName } from '../../models/index.js';
import type { AccessTokenPayload } from '../../types/auth.js';
import { ACCESS_TOKEN_TTL_SECONDS, HttpError } from '../../utils/index.js';

const ROLE_VALUES = new Set<string>(Object.values(RoleName));

export const signAccessToken = (payload: AccessTokenPayload): string =>
  jwt.sign({ ...payload }, env.JWT_SECRET, {
    algorithm: 'HS256',
    expiresIn: ACCESS_TOKEN_TTL_SECONDS,
  });

export const verifyAccessToken = (token: string): AccessTokenPayload => {
  try {
    const decoded = jwt.verify(token, env.JWT_SECRET, { algorithms: ['HS256'] });
    if (!isAccessTokenPayload(decoded)) {
      throw HttpError.unauthorized('Invalid token', 'UNAUTHENTICATED');
    }
    return decoded;
  } catch (error) {
    if (error instanceof HttpError) {
      throw error;
    }
    throw HttpError.unauthorized('Invalid token', 'UNAUTHENTICATED');
  }
};

const isAccessTokenPayload = (value: unknown): value is AccessTokenPayload => {
  if (typeof value !== 'object' || value === null) {
    return false;
  }
  const payload = value as Record<string, unknown>;
  return (
    typeof payload.sub === 'string' &&
    typeof payload.sid === 'string' &&
    payload.typ === 'access' &&
    Array.isArray(payload.roles) &&
    payload.roles.every((role) => typeof role === 'string' && ROLE_VALUES.has(role))
  );
};
