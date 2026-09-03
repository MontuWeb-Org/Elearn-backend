import type { Request, Response } from 'express';
import { asyncHandler, HttpError, requestMeta } from '../../utils/index.js';
import { getCurrentUser, login, refresh } from './auth.service.js';
import type {
  ForgotPasswordBody,
  LoginBody,
  RefreshBody,
  ResetPasswordBody,
  VerifyPasswordOtpBody,
} from './auth.schema.js';
import {
  requestPasswordReset,
  resetPassword,
  verifyPasswordOtp,
} from './password-reset.service.js';
import { revokeSession } from './session.service.js';

export const loginHandler = asyncHandler(async (req: Request, res: Response) => {
  const { email, password, remember_me } = req.body as LoginBody;
  const session = await login(email, password, remember_me, requestMeta(req));
  res.status(200).json(session);
});

export const refreshHandler = asyncHandler(async (req: Request, res: Response) => {
  const { refresh_token } = req.body as RefreshBody;
  const session = await refresh(refresh_token);
  res.status(200).json(session);
});

export const logoutHandler = asyncHandler(async (req: Request, res: Response) => {
  if (req.auth === undefined) {
    throw HttpError.unauthorized('Missing token', 'UNAUTHENTICATED');
  }
  await revokeSession(req.auth.sessionId);
  res.status(204).send();
});

export const meHandler = asyncHandler(async (req: Request, res: Response) => {
  if (req.auth === undefined) {
    throw HttpError.unauthorized('Missing token', 'UNAUTHENTICATED');
  }
  const user = await getCurrentUser(req.auth.userId);
  res.status(200).json(user);
});

export const forgotPasswordHandler = asyncHandler(async (req: Request, res: Response) => {
  const { email } = req.body as ForgotPasswordBody;
  await requestPasswordReset(email);
  res.status(202).json({});
});

export const verifyPasswordOtpHandler = asyncHandler(async (req: Request, res: Response) => {
  const { email, otp } = req.body as VerifyPasswordOtpBody;
  const result = await verifyPasswordOtp(email, otp);
  res.status(200).json(result);
});

export const resetPasswordHandler = asyncHandler(async (req: Request, res: Response) => {
  const { email, reset_token, password } = req.body as ResetPasswordBody;
  await resetPassword(email, reset_token, password);
  res.status(204).send();
});
