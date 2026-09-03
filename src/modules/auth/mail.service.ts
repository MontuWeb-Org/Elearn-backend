import nodemailer from 'nodemailer';
import type { Transporter } from 'nodemailer';
import { env, isProduction } from '../../config/env.js';
import { logger } from '../../utils/index.js';

let transporter: Transporter | undefined;

const getTransporter = (): Transporter | undefined => {
  const host = env.SMTP_HOST;
  if (host === undefined) {
    return undefined;
  }
  if (transporter === undefined) {
    const auth =
      env.SMTP_USER !== undefined && env.SMTP_PASS !== undefined
        ? { user: env.SMTP_USER, pass: env.SMTP_PASS }
        : undefined;
    transporter = nodemailer.createTransport({
      host,
      port: env.SMTP_PORT,
      secure: env.SMTP_SECURE,
      ...(auth !== undefined ? { auth } : {}),
    });
  }
  return transporter;
};

export const sendPasswordResetOtp = async (email: string, otp: string): Promise<void> => {
  const mailer = getTransporter();
  if (mailer !== undefined) {
    await mailer.sendMail({
      from: env.SMTP_FROM,
      to: email,
      subject: 'Your Montu password reset code',
      text: `Your password reset code is ${otp}. It expires in 10 minutes.`,
      html: `<p>Your password reset code is <strong>${otp}</strong>.</p><p>It expires in 10 minutes.</p>`,
    });
    logger.info(`Password reset OTP dispatched for ${email}`);
  } else if (isProduction) {
    logger.error('SMTP_HOST is not set; password reset OTP was not sent');
  }

  if (!isProduction) {
    logger.info(`Password reset OTP for ${email}: ${otp}`);
  }
};
