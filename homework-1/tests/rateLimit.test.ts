import request from 'supertest';
import express from 'express';
import { createRateLimiter } from '../src/middleware/rateLimiter.js';
import { router } from '../src/routes/index.js';
import { errorHandler } from '../src/middleware/errorHandler.js';
import { store } from '../src/store/transactionStore.js';

function createTestApp(max: number) {
  const testApp = express();
  testApp.use(express.json());
  testApp.use(createRateLimiter(max));
  testApp.use('/', router);
  testApp.use(errorHandler);
  return testApp;
}

beforeEach(() => {
  store.clear();
});

describe('Rate Limiting', () => {
  it('allows requests up to the configured limit', async () => {
    const testApp = createTestApp(3);

    for (let i = 0; i < 3; i++) {
      const res = await request(testApp).get('/transactions');
      expect(res.status).toBe(200);
    }
  });

  it('returns 429 when the limit is exceeded', async () => {
    const testApp = createTestApp(3);

    for (let i = 0; i < 3; i++) {
      await request(testApp).get('/transactions');
    }

    const res = await request(testApp).get('/transactions');
    expect(res.status).toBe(429);
    expect((res.body as { error: string }).error).toBeDefined();
  });

  it('includes rate limit headers in responses', async () => {
    const testApp = createTestApp(5);

    const res = await request(testApp).get('/transactions');
    expect(res.status).toBe(200);
    expect(res.headers['ratelimit-limit'] ?? res.headers['x-ratelimit-limit']).toBeDefined();
  });
});
