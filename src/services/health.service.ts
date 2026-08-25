import { isDatabaseHealthy } from '../config/database.js';
import { env } from '../config/env.js';

export interface HealthReport {
  status: 'ok' | 'degraded';
  uptime: number;
  environment: string;
  timestamp: string;
  dependencies: {
    database: 'up' | 'down';
  };
}

export const getHealthReport = async (): Promise<HealthReport> => {
  const databaseUp = await isDatabaseHealthy();

  return {
    status: databaseUp ? 'ok' : 'degraded',
    uptime: Math.round(process.uptime()),
    environment: env.NODE_ENV,
    timestamp: new Date().toISOString(),
    dependencies: { database: databaseUp ? 'up' : 'down' },
  };
};
