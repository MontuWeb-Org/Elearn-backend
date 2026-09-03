import type { Request, Response } from 'express';
import { asyncHandler } from '../../utils/index.js';
import { getHealthReport } from './health.service.js';

/** Liveness: the process is up and serving. */
export const live = (_req: Request, res: Response): void => {
  res.status(200).json({ status: 'ok' });
};

/** Readiness: the process and its dependencies (PostgreSQL) are usable. */
export const ready = asyncHandler(async (_req: Request, res: Response) => {
  const report = await getHealthReport();
  res.status(report.status === 'ok' ? 200 : 503).json(report);
});
