import { jest } from '@jest/globals';
import bcrypt from 'bcrypt';
import request from 'supertest';
import { callArg, prismaMock, resetPrismaMock } from '../helpers/prisma-mock.js';
import { buildUser, TEST_PASSWORD } from '../helpers/fixtures.js';

const sendPasswordResetOtp = jest.fn<(email: string, otp: string) => Promise<void>>();
jest.unstable_mockModule('../../src/modules/auth/mail.service.js', () => ({
  sendPasswordResetOtp,
}));

const { createApp } = await import('../../src/app.js');
const { cache } = await import('../../src/config/cache.js');
const { sha256Hex } = await import('../../src/utils/crypto.js');
const { PASSWORD_RESET_MAX_ATTEMPTS, PASSWORD_RESET_TTL_SECONDS } =
  await import('../../src/utils/constants.js');

const app = createApp();
const FORGOT_URL = '/api/v1/auth/password/forgot';
const VERIFY_URL = '/api/v1/auth/password/otp/verify';
const RESET_URL = '/api/v1/auth/password/reset';

const user = buildUser();
const cacheKey = `pwdreset:${user.id}`;
const NEW_PASSWORD = 'BrandNewSecret!45';

interface UserUpdateArgs {
  where: { id: string };
  data: { passwordHash: string };
}

/** Drives the forgot step and returns the OTP that was mailed out. */
const requestOtp = async (): Promise<string> => {
  await request(app).post(FORGOT_URL).send({ email: user.email });
  const call = sendPasswordResetOtp.mock.calls.at(-1);
  if (call === undefined) {
    throw new Error('no OTP was dispatched');
  }
  return call[1];
};

/** Drives forgot + verify and returns the single-use reset token. */
const requestResetToken = async (): Promise<string> => {
  const otp = await requestOtp();
  const response = await request(app).post(VERIFY_URL).send({ email: user.email, otp });
  return response.body.reset_token as string;
};

beforeEach(() => {
  resetPrismaMock();
  // `clearMocks` wipes call history but keeps implementations, so the transport
  // has to be put back to its happy path explicitly.
  sendPasswordResetOtp.mockResolvedValue(undefined);
  cache.delete(cacheKey);
  prismaMock.user.findUnique.mockResolvedValue(user);
});

describe('POST /api/v1/auth/password/forgot', () => {
  it('accepts the request and mails a six-digit code', async () => {
    const response = await request(app).post(FORGOT_URL).send({ email: user.email });

    expect(response.status).toBe(202);
    expect(response.body).toEqual({});
    expect(sendPasswordResetOtp).toHaveBeenCalledTimes(1);
    expect(sendPasswordResetOtp).toHaveBeenCalledWith(user.email, expect.stringMatching(/^\d{6}$/));
  });

  it('stores only a hash of the code, never the code itself', async () => {
    const otp = await requestOtp();

    const entry = cache.get<{ kind: string; otpHash: string; attempts: number }>(cacheKey);
    expect(entry).toEqual({ kind: 'otp', otpHash: sha256Hex(otp), attempts: 0 });
    expect(JSON.stringify(entry)).not.toContain(otp);
  });

  it('answers identically for an unknown email so accounts cannot be enumerated', async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);

    const response = await request(app).post(FORGOT_URL).send({ email: 'ghost@montu.test' });

    expect(response.status).toBe(202);
    expect(response.body).toEqual({});
    expect(sendPasswordResetOtp).not.toHaveBeenCalled();
  });

  it('still accepts the request when the mail transport fails', async () => {
    sendPasswordResetOtp.mockRejectedValue(new Error('smtp down'));
    const logged = jest.spyOn(console, 'error').mockImplementation(() => undefined);

    const response = await request(app).post(FORGOT_URL).send({ email: user.email });

    expect(response.status).toBe(202);
    expect(logged).toHaveBeenCalled();
    logged.mockRestore();
  });

  it('lower-cases the email before the lookup', async () => {
    await request(app).post(FORGOT_URL).send({ email: '  TEACHER@Montu.TEST ' });

    const args = callArg<{ where: { email: string } }>(prismaMock.user.findUnique);
    expect(args.where.email).toBe('teacher@montu.test');
  });

  it('rejects a malformed email with 400', async () => {
    const response = await request(app).post(FORGOT_URL).send({ email: 'nope' });

    expect(response.status).toBe(400);
    expect(response.body.error.code).toBe('VALIDATION_ERROR');
  });
});

describe('POST /api/v1/auth/password/otp/verify', () => {
  it('exchanges a correct code for a single-use reset token', async () => {
    const otp = await requestOtp();

    const response = await request(app).post(VERIFY_URL).send({ email: user.email, otp });

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      reset_token: expect.any(String),
      expires_in: PASSWORD_RESET_TTL_SECONDS,
    });

    const entry = cache.get<{ kind: string; resetTokenHash: string }>(cacheKey);
    expect(entry).toEqual({
      kind: 'reset',
      resetTokenHash: sha256Hex(response.body.reset_token as string),
    });
  });

  it('rejects a wrong code and keeps the pending request alive', async () => {
    const otp = await requestOtp();
    const wrong = otp === '000000' ? '111111' : '000000';

    const response = await request(app).post(VERIFY_URL).send({ email: user.email, otp: wrong });

    expect(response.status).toBe(401);
    expect(response.body.error.code).toBe('INVALID_OTP');

    const retry = await request(app).post(VERIFY_URL).send({ email: user.email, otp });
    expect(retry.status).toBe(200);
  });

  it(`burns the request after ${PASSWORD_RESET_MAX_ATTEMPTS} wrong codes`, async () => {
    const otp = await requestOtp();
    const wrong = otp === '000000' ? '111111' : '000000';

    for (let attempt = 1; attempt < PASSWORD_RESET_MAX_ATTEMPTS; attempt += 1) {
      const response = await request(app).post(VERIFY_URL).send({ email: user.email, otp: wrong });
      expect(response.status).toBe(401);
    }

    const final = await request(app).post(VERIFY_URL).send({ email: user.email, otp: wrong });
    expect(final.status).toBe(410);
    expect(final.body.error.code).toBe('OTP_EXPIRED');

    // Even the correct code is worthless now.
    const afterBurn = await request(app).post(VERIFY_URL).send({ email: user.email, otp });
    expect(afterBurn.status).toBe(410);
    expect(cache.get(cacheKey)).toBeUndefined();
  });

  it('reports 410 when no reset was requested', async () => {
    const response = await request(app).post(VERIFY_URL).send({ email: user.email, otp: '123456' });

    expect(response.status).toBe(410);
    expect(response.body.error.code).toBe('OTP_EXPIRED');
  });

  it('refuses to replay a code that was already exchanged', async () => {
    const otp = await requestOtp();
    await request(app).post(VERIFY_URL).send({ email: user.email, otp });

    const replay = await request(app).post(VERIFY_URL).send({ email: user.email, otp });

    expect(replay.status).toBe(410);
    expect(replay.body.error.code).toBe('OTP_EXPIRED');
  });

  it('rejects an unknown email as an invalid code', async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);

    const response = await request(app)
      .post(VERIFY_URL)
      .send({ email: 'ghost@montu.test', otp: '123456' });

    expect(response.status).toBe(401);
    expect(response.body.error.code).toBe('INVALID_OTP');
  });

  it.each([
    ['too short', '12345'],
    ['too long', '1234567'],
    ['non-numeric', '12a456'],
    ['empty', ''],
  ])('rejects a %s code with 400', async (_label, otp) => {
    const response = await request(app).post(VERIFY_URL).send({ email: user.email, otp });

    expect(response.status).toBe(400);
    expect(response.body.error.code).toBe('VALIDATION_ERROR');
  });
});

describe('POST /api/v1/auth/password/reset', () => {
  it('stores a bcrypt hash of the new password and revokes every session', async () => {
    const resetToken = await requestResetToken();

    const response = await request(app)
      .post(RESET_URL)
      .send({ email: user.email, reset_token: resetToken, password: NEW_PASSWORD });

    expect(response.status).toBe(204);
    expect(prismaMock.$transaction).toHaveBeenCalledTimes(1);

    const update = callArg<UserUpdateArgs>(prismaMock.user.update);
    expect(update.where.id).toBe(user.id);
    expect(update.data.passwordHash).not.toBe(NEW_PASSWORD);
    expect(update.data.passwordHash).toMatch(/^\$2[aby]\$/);
    await expect(bcrypt.compare(NEW_PASSWORD, update.data.passwordHash)).resolves.toBe(true);
    await expect(bcrypt.compare(TEST_PASSWORD, update.data.passwordHash)).resolves.toBe(false);

    expect(callArg(prismaMock.userSession.updateMany)).toEqual({
      where: { userId: user.id, isRevoked: false },
      data: { isRevoked: true },
    });
  });

  it('consumes the reset token so it cannot be replayed', async () => {
    const resetToken = await requestResetToken();
    await request(app)
      .post(RESET_URL)
      .send({ email: user.email, reset_token: resetToken, password: NEW_PASSWORD });

    const replay = await request(app)
      .post(RESET_URL)
      .send({ email: user.email, reset_token: resetToken, password: NEW_PASSWORD });

    expect(replay.status).toBe(410);
    expect(replay.body.error.code).toBe('OTP_EXPIRED');
    expect(cache.get(cacheKey)).toBeUndefined();
  });

  it('rejects a reset token that does not match the pending request', async () => {
    await requestResetToken();

    const response = await request(app)
      .post(RESET_URL)
      .send({ email: user.email, reset_token: 'forged-token', password: NEW_PASSWORD });

    expect(response.status).toBe(401);
    expect(response.body.error.code).toBe('INVALID_OTP');
    expect(prismaMock.user.update).not.toHaveBeenCalled();
  });

  it('refuses to skip the OTP step', async () => {
    const otp = await requestOtp();

    const response = await request(app)
      .post(RESET_URL)
      .send({ email: user.email, reset_token: otp, password: NEW_PASSWORD });

    expect(response.status).toBe(401);
    expect(response.body.error.code).toBe('INVALID_OTP');
    expect(prismaMock.user.update).not.toHaveBeenCalled();
  });

  it('reports 410 when there is no pending reset at all', async () => {
    const response = await request(app)
      .post(RESET_URL)
      .send({ email: user.email, reset_token: 'anything', password: NEW_PASSWORD });

    expect(response.status).toBe(410);
    expect(response.body.error.code).toBe('OTP_EXPIRED');
  });

  it('rejects an unknown email', async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);

    const response = await request(app)
      .post(RESET_URL)
      .send({ email: 'ghost@montu.test', reset_token: 'anything', password: NEW_PASSWORD });

    expect(response.status).toBe(401);
    expect(response.body.error.code).toBe('INVALID_OTP');
  });

  it.each([
    ['a password below the minimum length', { password: 'short1!' }, 'password'],
    ['a missing password', {}, 'password'],
    ['a missing reset token', { reset_token: undefined, password: NEW_PASSWORD }, 'reset_token'],
  ])('rejects %s with 400', async (_label, overrides, field) => {
    const response = await request(app)
      .post(RESET_URL)
      .send({ email: user.email, reset_token: 'anything', ...overrides });

    expect(response.status).toBe(400);
    expect(response.body.error.code).toBe('VALIDATION_ERROR');
    expect(response.body.error.details).toEqual(
      expect.arrayContaining([expect.objectContaining({ field })]),
    );
  });
});
