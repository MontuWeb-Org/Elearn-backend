import { prisma } from '../../config/database.js';
import type { RequestMeta, SessionDto } from '../../types/auth.js';
import {
  encodeCursor,
  generateRefreshToken,
  HttpError,
  REFRESH_TOKEN_REMEMBER_TTL_DAYS,
  REFRESH_TOKEN_TTL_DAYS,
  sha256Hex,
  type CursorPayload,
} from '../../utils/index.js';

const refreshTtlDays = (rememberMe: boolean): number =>
  rememberMe ? REFRESH_TOKEN_REMEMBER_TTL_DAYS : REFRESH_TOKEN_TTL_DAYS;

const expiresAtFrom = (rememberMe: boolean, from = new Date()): Date => {
  const expires = new Date(from);
  expires.setUTCDate(expires.getUTCDate() + refreshTtlDays(rememberMe));
  return expires;
};

export const createSession = async (
  userId: string,
  rememberMe: boolean,
  meta: RequestMeta,
): Promise<{ sessionId: string; refreshToken: string }> => {
  const refreshToken = generateRefreshToken();

  const session = await prisma.userSession.create({
    data: {
      userId,
      refreshTokenHash: sha256Hex(refreshToken),
      rememberMe,
      expiresAt: expiresAtFrom(rememberMe),
      ...(meta.userAgent !== undefined ? { userAgent: meta.userAgent } : {}),
      ...(meta.ipAddress !== undefined ? { ipAddress: meta.ipAddress } : {}),
    },
  });

  return { sessionId: session.id, refreshToken };
};

export const rotateSession = async (
  refreshToken: string,
): Promise<{ sessionId: string; userId: string; refreshToken: string } | null> => {
  const existing = await prisma.userSession.findUnique({
    where: { refreshTokenHash: sha256Hex(refreshToken) },
  });

  if (existing === null || existing.isRevoked || existing.expiresAt.getTime() <= Date.now()) {
    return null;
  }

  const nextRefreshToken = generateRefreshToken();
  await prisma.userSession.update({
    where: { id: existing.id },
    data: {
      refreshTokenHash: sha256Hex(nextRefreshToken),
      expiresAt: expiresAtFrom(existing.rememberMe),
    },
  });

  return { sessionId: existing.id, userId: existing.userId, refreshToken: nextRefreshToken };
};

export const revokeSession = async (sessionId: string): Promise<void> => {
  await prisma.userSession.updateMany({
    where: { id: sessionId, isRevoked: false },
    data: { isRevoked: true },
  });
};

export const findActiveSession = async (sessionId: string) =>
  prisma.userSession.findFirst({
    where: {
      id: sessionId,
      isRevoked: false,
      expiresAt: { gt: new Date() },
    },
    include: { user: true },
  });

export const listActiveSessions = async (
  userId: string,
  currentSessionId: string,
  options: { limit: number; cursor?: CursorPayload },
): Promise<{
  data: SessionDto[];
  total: number;
  nextCursor: string | null;
}> => {
  const now = new Date();
  const activeWhere = {
    userId,
    isRevoked: false,
    expiresAt: { gt: now },
  };

  const cursorWhere =
    options.cursor === undefined
      ? {}
      : {
          OR: [
            { createdAt: { lt: new Date(options.cursor.createdAt) } },
            {
              createdAt: new Date(options.cursor.createdAt),
              id: { lt: options.cursor.id },
            },
          ],
        };

  const [total, rows] = await Promise.all([
    prisma.userSession.count({ where: activeWhere }),
    prisma.userSession.findMany({
      where: { ...activeWhere, ...cursorWhere },
      orderBy: [{ createdAt: 'desc' }, { id: 'desc' }],
      take: options.limit + 1,
    }),
  ]);

  const hasMore = rows.length > options.limit;
  const page = hasMore ? rows.slice(0, options.limit) : rows;
  const last = page.at(-1);

  return {
    total,
    nextCursor: hasMore && last !== undefined ? encodeCursor(last.id, last.createdAt) : null,
    data: page.map((session) => ({
      user_session_id: session.id,
      user_agent: session.userAgent,
      ip_address: session.ipAddress,
      is_revoked: session.isRevoked,
      remember_me: session.rememberMe,
      is_current: session.id === currentSessionId,
      expires_at: session.expiresAt.toISOString(),
      created_at: session.createdAt.toISOString(),
    })),
  };
};

export const revokeOwnedSession = async (userId: string, sessionId: string): Promise<void> => {
  const result = await prisma.userSession.updateMany({
    where: { id: sessionId, userId, isRevoked: false },
    data: { isRevoked: true },
  });

  if (result.count === 0) {
    throw HttpError.notFound('Session not found');
  }
};
