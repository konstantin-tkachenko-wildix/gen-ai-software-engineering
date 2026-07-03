import rateLimit from 'express-rate-limit';

export function createRateLimiter(max: number) {
  return rateLimit({
    windowMs: 60 * 1000,
    max,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many requests', retryAfter: 60 },
  });
}
