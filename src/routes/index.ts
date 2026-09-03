import { Router } from 'express';
import { authRouter } from '../modules/auth/auth.routes.js';
import { meRouter } from '../modules/auth/me.routes.js';
import { healthRouter } from '../modules/health/health.routes.js';

export const apiRouter: Router = Router();

apiRouter.use('/health', healthRouter);
apiRouter.use('/auth', authRouter);
apiRouter.use('/me', meRouter);
