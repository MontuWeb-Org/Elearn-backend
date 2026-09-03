import { createHash, randomBytes, randomInt } from 'node:crypto';

/** 32 random bytes, base64url — the raw refresh token sent to the client. */
export const generateRefreshToken = (): string => randomBytes(32).toString('base64url');

/** 6-digit code, cryptographically random, including leading zeros. */
export const generateOtp = (): string => randomInt(0, 1_000_000).toString().padStart(6, '0');

export const sha256Hex = (value: string): string =>
  createHash('sha256').update(value).digest('hex');
