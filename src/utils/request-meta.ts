import type { Request } from 'express';
import type { RequestMeta } from '../types/auth.js';

export const requestMeta = (req: Request): RequestMeta => {
  const forwarded = req.headers['x-forwarded-for'];
  const forwardedIp = typeof forwarded === 'string' ? forwarded.split(',')[0]?.trim() : undefined;

  const meta: RequestMeta = {};
  const userAgent = req.headers['user-agent'];
  if (userAgent !== undefined && userAgent.length > 0) {
    meta.userAgent = userAgent;
  }

  const ipAddress = forwardedIp ?? req.ip;
  if (ipAddress !== undefined && ipAddress.length > 0) {
    meta.ipAddress = ipAddress;
  }

  return meta;
};
