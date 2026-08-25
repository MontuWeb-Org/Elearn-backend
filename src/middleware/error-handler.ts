import type { ErrorRequestHandler } from 'express';
import { Prisma } from '@prisma/client';
import { ZodError } from 'zod';
import { HttpError } from '../utils/http-error.js';
import { isProduction } from '../config/env.js';
import { logger } from '../utils/logger.js';

interface ErrorBody {
  status: 'error';
  message: string;
  details?: unknown;
  stack?: string;
}

const resolve = (error: unknown): { statusCode: number; message: string; details?: unknown } => {
  if (error instanceof HttpError) {
    return { statusCode: error.statusCode, message: error.message, details: error.details };
  }
  if (error instanceof ZodError) {
    return { statusCode: 400, message: 'Validation failed', details: error.issues };
  }
  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    // P2002 unique constraint, P2025 record not found.
    if (error.code === 'P2002') {
      return { statusCode: 409, message: 'Resource already exists' };
    }
    if (error.code === 'P2025') {
      return { statusCode: 404, message: 'Resource not found' };
    }
    return { statusCode: 400, message: 'Database request error' };
  }
  return { statusCode: 500, message: 'Internal Server Error' };
};

export const errorHandler: ErrorRequestHandler = (error, req, res, _next) => {
  const { statusCode, message, details } = resolve(error);

  if (statusCode >= 500) {
    logger.error(`${req.method} ${req.originalUrl} -> ${statusCode}`, error);
  } else {
    logger.warn(`${req.method} ${req.originalUrl} -> ${statusCode}: ${message}`);
  }

  const body: ErrorBody = { status: 'error', message };
  if (details !== undefined) {
    body.details = details;
  }
  if (!isProduction && error instanceof Error && error.stack !== undefined) {
    body.stack = error.stack;
  }

  res.status(statusCode).json(body);
};
