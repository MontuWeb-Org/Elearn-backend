import type { Server } from 'node:http';
import { createApp } from './app.js';
import { env } from './config/env.js';
import { connectDatabase, disconnectDatabase } from './config/database.js';
import { logger } from './utils/index.js';

const shutdown = (server: Server, signal: string): void => {
  logger.info(`${signal} received, shutting down`);

  const forceExit = setTimeout(() => {
    logger.error('Graceful shutdown timed out, forcing exit');
    process.exit(1);
  }, 10_000);
  forceExit.unref();

  server.close((closeError) => {
    void (async (): Promise<void> => {
      if (closeError) {
        logger.error('Error while closing HTTP server', closeError);
      }
      await disconnectDatabase().catch((error: unknown) => {
        logger.error('Error while disconnecting the database', error);
      });
      process.exit(closeError ? 1 : 0);
    })();
  });
};

const start = async (): Promise<void> => {
  await connectDatabase();

  const server = createApp().listen(env.PORT, () => {
    logger.info(`Server listening on http://localhost:${env.PORT} (${env.NODE_ENV})`);
  });

  for (const signal of ['SIGINT', 'SIGTERM'] as const) {
    process.on(signal, () => {
      shutdown(server, signal);
    });
  }
};

start().catch((error: unknown) => {
  logger.error('Failed to start the server', error);
  process.exit(1);
});
