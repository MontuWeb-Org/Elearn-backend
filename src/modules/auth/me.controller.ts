import type { Request, Response } from 'express';
import { asyncHandler, decodeCursor, HttpError, pageEnvelope } from '../../utils/index.js';
import type { SessionIdParams, SessionListQuery } from './auth.schema.js';
import { listActiveSessions, revokeOwnedSession } from './session.service.js';

export const listSessionsHandler = asyncHandler(async (req: Request, res: Response) => {
  if (req.auth === undefined) {
    throw HttpError.unauthorized('Missing token', 'UNAUTHENTICATED');
  }

  const query = req.validatedQuery as SessionListQuery;
  const cursor = query.cursor === undefined ? undefined : decodeCursor(query.cursor);
  const result = await listActiveSessions(req.auth.userId, req.auth.sessionId, {
    limit: query.limit,
    ...(cursor !== undefined ? { cursor } : {}),
  });

  res.status(200).json(
    pageEnvelope(result.data, {
      limit: query.limit,
      cursor: query.cursor ?? null,
      next_cursor: result.nextCursor,
      total: result.total,
    }),
  );
});

export const revokeSessionHandler = asyncHandler(async (req: Request, res: Response) => {
  if (req.auth === undefined) {
    throw HttpError.unauthorized('Missing token', 'UNAUTHENTICATED');
  }

  const { sessionId } = req.validatedParams as SessionIdParams;
  await revokeOwnedSession(req.auth.userId, sessionId);
  res.status(204).send();
});
