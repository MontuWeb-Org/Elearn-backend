import type { AuthContext } from './auth.js';

declare module 'express-serve-static-core' {
  interface Request {
    auth?: AuthContext;
    validatedQuery?: unknown;
    validatedParams?: unknown;
  }
}
