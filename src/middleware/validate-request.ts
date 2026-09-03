import type { NextFunction, Request, Response } from 'express';
import type { z } from 'zod';

export const validateBody =
  (schema: z.ZodType) =>
  (req: Request, _res: Response, next: NextFunction): void => {
    req.body = schema.parse(req.body);
    next();
  };

export const validateQuery =
  (schema: z.ZodType) =>
  (req: Request, _res: Response, next: NextFunction): void => {
    req.validatedQuery = schema.parse(req.query);
    next();
  };

export const validateParams =
  (schema: z.ZodType) =>
  (req: Request, _res: Response, next: NextFunction): void => {
    req.validatedParams = schema.parse(req.params);
    next();
  };
