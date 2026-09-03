import { Router } from 'express';
import { requireAuth, requireRole, validateBody } from '../../middleware/index.js';
import { RoleName } from '../../models/index.js';
import {
  forgotPasswordHandler,
  loginHandler,
  logoutHandler,
  meHandler,
  refreshHandler,
  resetPasswordHandler,
  verifyPasswordOtpHandler,
} from './auth.controller.js';
import {
  forgotPasswordSchema,
  loginSchema,
  refreshSchema,
  resetPasswordSchema,
  verifyPasswordOtpSchema,
} from './auth.schema.js';

export const authRouter: Router = Router();

authRouter.post('/login', validateBody(loginSchema), loginHandler);
authRouter.post('/refresh', validateBody(refreshSchema), refreshHandler);
authRouter.post('/logout', requireAuth, logoutHandler);
authRouter.get(
  '/me',
  requireAuth,
  requireRole(
    RoleName.TEACHER,
    RoleName.ASSISTANT,
    RoleName.PARENT,
    RoleName.STUDENT,
    RoleName.ADMIN,
  ),
  meHandler,
);
authRouter.post('/password/forgot', validateBody(forgotPasswordSchema), forgotPasswordHandler);
authRouter.post(
  '/password/otp/verify',
  validateBody(verifyPasswordOtpSchema),
  verifyPasswordOtpHandler,
);
authRouter.post('/password/reset', validateBody(resetPasswordSchema), resetPasswordHandler);
