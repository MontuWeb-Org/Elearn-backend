/* eslint-disable no-console -- this module is the single sanctioned console wrapper */
import { env } from '../config/env.js';

type Level = 'debug' | 'info' | 'warn' | 'error';

const levelRank: Record<Level, number> = { debug: 10, info: 20, warn: 30, error: 40 };

const shouldLog = (level: Level): boolean => levelRank[level] >= levelRank[env.LOG_LEVEL];

const write = (level: Level, message: string, meta?: unknown): void => {
  if (!shouldLog(level)) return;
  const line = `${new Date().toISOString()} [${level.toUpperCase()}] ${message}`;
  const stream = level === 'error' || level === 'warn' ? console.error : console.log;
  if (meta === undefined) {
    stream(line);
  } else {
    stream(line, meta);
  }
};

export const logger = {
  debug: (message: string, meta?: unknown): void => write('debug', message, meta),
  info: (message: string, meta?: unknown): void => write('info', message, meta),
  warn: (message: string, meta?: unknown): void => write('warn', message, meta),
  error: (message: string, meta?: unknown): void => write('error', message, meta),
};
