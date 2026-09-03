import { cache } from '../../config/cache.js';
import { prisma } from '../../config/database.js';
import {
  generateOtp,
  generateRefreshToken,
  HttpError,
  logger,
  PASSWORD_RESET_CACHE_PREFIX,
  PASSWORD_RESET_MAX_ATTEMPTS,
  PASSWORD_RESET_TTL_SECONDS,
  sha256Hex,
} from '../../utils/index.js';
import { sendPasswordResetOtp } from './mail.service.js';
import { hashPassword } from './password.service.js';

const TTL_MS = PASSWORD_RESET_TTL_SECONDS * 1000;

type ResetEntry =
  { kind: 'otp'; otpHash: string; attempts: number } | { kind: 'reset'; resetTokenHash: string };

const cacheKey = (userId: string): string => `${PASSWORD_RESET_CACHE_PREFIX}${userId}`;

const invalidOtp = (): HttpError => HttpError.unauthorized('Invalid OTP', 'INVALID_OTP');

const expiredOtp = (): HttpError => HttpError.gone('OTP expired', 'OTP_EXPIRED');

const findUserByEmail = async (email: string) =>
  prisma.user.findUnique({ where: { email: email.toLowerCase() } });

export const requestPasswordReset = async (email: string): Promise<void> => {
  const user = await findUserByEmail(email);
  if (user === null) {
    return;
  }

  const otp = generateOtp();
  cache.set<ResetEntry>(
    cacheKey(user.id),
    { kind: 'otp', otpHash: sha256Hex(otp), attempts: 0 },
    TTL_MS,
  );

  try {
    await sendPasswordResetOtp(user.email, otp);
  } catch (error) {
    logger.error('Failed to send password reset OTP', error);
  }
};

export const verifyPasswordOtp = async (
  email: string,
  otp: string,
): Promise<{ reset_token: string; expires_in: number }> => {
  const user = await findUserByEmail(email);
  if (user === null) {
    throw invalidOtp();
  }

  const key = cacheKey(user.id);
  const entry = cache.get<ResetEntry>(key);
  if (entry === undefined) {
    throw expiredOtp();
  }
  if (entry.kind !== 'otp') {
    throw expiredOtp();
  }

  if (entry.otpHash !== sha256Hex(otp)) {
    const attempts = entry.attempts + 1;
    if (attempts >= PASSWORD_RESET_MAX_ATTEMPTS) {
      cache.delete(key);
      throw expiredOtp();
    }
    cache.update<ResetEntry>(key, { kind: 'otp', otpHash: entry.otpHash, attempts });
    throw invalidOtp();
  }

  const resetToken = generateRefreshToken();
  cache.set<ResetEntry>(key, { kind: 'reset', resetTokenHash: sha256Hex(resetToken) }, TTL_MS);

  return { reset_token: resetToken, expires_in: PASSWORD_RESET_TTL_SECONDS };
};

export const resetPassword = async (
  email: string,
  resetToken: string,
  password: string,
): Promise<void> => {
  const user = await findUserByEmail(email);
  if (user === null) {
    throw invalidOtp();
  }

  const key = cacheKey(user.id);
  const entry = cache.get<ResetEntry>(key);
  if (entry === undefined) {
    throw expiredOtp();
  }
  if (entry.kind !== 'reset' || entry.resetTokenHash !== sha256Hex(resetToken)) {
    throw invalidOtp();
  }

  const passwordHash = await hashPassword(password);

  await prisma.$transaction([
    prisma.user.update({
      where: { id: user.id },
      data: { passwordHash },
    }),
    prisma.userSession.updateMany({
      where: { userId: user.id, isRevoked: false },
      data: { isRevoked: true },
    }),
  ]);

  cache.delete(key);
};
