import { Router } from 'express';
import { requireAuth, validateParams, validateQuery } from '../../middleware/index.js';
import { sessionIdParamsSchema, sessionListQuerySchema } from './auth.schema.js';
import { listSessionsHandler, revokeSessionHandler } from './me.controller.js';

export const meRouter: Router = Router();

meRouter.use(requireAuth);
meRouter.get('/sessions', validateQuery(sessionListQuerySchema), listSessionsHandler);
meRouter.delete(
  '/sessions/:sessionId',
  validateParams(sessionIdParamsSchema),
  revokeSessionHandler,
);
