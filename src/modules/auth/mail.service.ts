import { isProduction } from '../../config/env.js';
import { logger } from '../../utils/index.js';

/**
 * Outbound mail is not wired to an SMTP provider yet. Development logs the OTP
 * so the three-screen reset flow can be exercised; production only logs that a
 * send was attempted.
 */
export const sendPasswordResetOtp = (email: string, otp: string): Promise<void> => {
  if (!isProduction) {
    logger.info(`Password reset OTP for ${email}: ${otp}`);
  } else {
    logger.info(`Password reset OTP dispatched for ${email}`);
  }
  return Promise.resolve();
};
