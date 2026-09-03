import type { ErrorRequestHandler } from 'express';
import { Prisma } from '@prisma/client';
import { ZodError } from 'zod';
import { isProduction } from '../config/env.js';
import { HttpError, logger } from '../utils/index.js';

interface ErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
  stack?: string;
}

const resolve = (
  error: unknown,
): { statusCode: number; code: string; message: string; details?: unknown } => {
  if (error instanceof HttpError) {
    return {
      statusCode: error.statusCode,
      code: error.code,
      message: error.message,
      details: error.details,
    };
  }
  if (error instanceof ZodError) {
    return {
      statusCode: 400,
      code: 'VALIDATION_ERROR',
      message: 'Validation failed',
      details: error.issues.map((issue) => ({
        field: issue.path.join('.'),
        issue: issue.message,
      })),
    };
  }
  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    if (error.code === 'P2002') {
      return { statusCode: 409, code: 'CONFLICT', message: 'Resource already exists' };
    }
    if (error.code === 'P2025') {
      return { statusCode: 404, code: 'NOT_FOUND', message: 'Resource not found' };
    }
    return { statusCode: 400, code: 'VALIDATION_ERROR', message: 'Database request error' };
  }
  return { statusCode: 500, code: 'INTERNAL_ERROR', message: 'Internal Server Error' };
};

export const errorHandler: ErrorRequestHandler = (error, req, res, _next) => {
  const { statusCode, code, message, details } = resolve(error);

  if (statusCode >= 500) {
    logger.error(`${req.method} ${req.originalUrl} -> ${statusCode}`, error);
  } else {
    logger.warn(`${req.method} ${req.originalUrl} -> ${statusCode}: ${message}`);
  }

  const body: ErrorBody = { error: { code, message } };
  if (details !== undefined) {
    body.error.details = details;
  }
  if (!isProduction && error instanceof Error && error.stack !== undefined) {
    body.stack = error.stack;
  }

  res.status(statusCode).json(body);
};
