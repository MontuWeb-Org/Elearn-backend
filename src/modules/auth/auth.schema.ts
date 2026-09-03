import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().trim().toLowerCase().email(),
  password: z.string().min(1),
  remember_me: z.boolean().default(false),
});

export const refreshSchema = z.object({
  refresh_token: z.string().min(1),
});

export const forgotPasswordSchema = z.object({
  email: z.string().trim().toLowerCase().email(),
});

export const verifyPasswordOtpSchema = z.object({
  email: z.string().trim().toLowerCase().email(),
  otp: z.string().regex(/^[0-9]{6}$/),
});

export const resetPasswordSchema = z.object({
  email: z.string().trim().toLowerCase().email(),
  reset_token: z.string().min(1),
  password: z.string().min(8),
});

export const sessionListQuerySchema = z.object({
  limit: z.coerce.number().int().min(1).max(100).default(25),
  cursor: z.string().min(1).optional(),
});

export const sessionIdParamsSchema = z.object({
  sessionId: z.string().uuid(),
});

export type LoginBody = z.infer<typeof loginSchema>;
export type RefreshBody = z.infer<typeof refreshSchema>;
export type ForgotPasswordBody = z.infer<typeof forgotPasswordSchema>;
export type VerifyPasswordOtpBody = z.infer<typeof verifyPasswordOtpSchema>;
export type ResetPasswordBody = z.infer<typeof resetPasswordSchema>;
export type SessionListQuery = z.infer<typeof sessionListQuerySchema>;
export type SessionIdParams = z.infer<typeof sessionIdParamsSchema>;
