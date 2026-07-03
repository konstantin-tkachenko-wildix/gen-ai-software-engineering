import express from 'express';
import { router } from './routes/index.js';
import { createRateLimiter } from './middleware/rateLimiter.js';
import { errorHandler } from './middleware/errorHandler.js';

const app = express();

app.use(express.json());

if (process.env.NODE_ENV !== 'test') {
  app.use(createRateLimiter(100));
}

app.use('/', router);
app.use(errorHandler);

export { app };
