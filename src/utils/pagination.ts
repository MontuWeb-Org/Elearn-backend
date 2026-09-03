import { HttpError } from './http-error.js';

export interface CursorPayload {
  id: string;
  createdAt: string;
}

export interface PageMeta {
  limit: number;
  cursor: string | null;
  next_cursor: string | null;
  total: number;
}

export const encodeCursor = (id: string, createdAt: Date): string =>
  Buffer.from(JSON.stringify({ id, createdAt: createdAt.toISOString() }), 'utf8').toString(
    'base64url',
  );

export const decodeCursor = (raw: string): CursorPayload => {
  try {
    const parsed: unknown = JSON.parse(Buffer.from(raw, 'base64url').toString('utf8'));
    if (
      typeof parsed !== 'object' ||
      parsed === null ||
      !('id' in parsed) ||
      !('createdAt' in parsed) ||
      typeof parsed.id !== 'string' ||
      typeof parsed.createdAt !== 'string'
    ) {
      throw new Error('invalid');
    }
    return { id: parsed.id, createdAt: parsed.createdAt };
  } catch {
    throw HttpError.badRequest('Invalid cursor');
  }
};

export const pageEnvelope = <T>(data: T[], page: PageMeta): { data: T[]; page: PageMeta } => ({
  data,
  page,
});
