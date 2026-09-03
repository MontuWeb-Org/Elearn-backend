import bcrypt from 'bcrypt';
import { env } from '../../config/env.js';

/** Pre-hashed dummy used when the email is unknown so compare cost stays similar. */
const TIMING_PAD_HASH = bcrypt.hash('timing-pad', env.BCRYPT_ROUNDS);

export const hashPassword = async (plain: string): Promise<string> =>
  bcrypt.hash(plain, env.BCRYPT_ROUNDS);

export const verifyPassword = async (plain: string, passwordHash: string): Promise<boolean> =>
  bcrypt.compare(plain, passwordHash);

export const dummyPasswordCheck = async (plain: string): Promise<void> => {
  await bcrypt.compare(plain, await TIMING_PAD_HASH);
};
