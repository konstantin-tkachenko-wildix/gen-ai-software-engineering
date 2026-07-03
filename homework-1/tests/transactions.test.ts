import request from 'supertest';
import { app } from '../src/app.js';
import { store } from '../src/store/transactionStore.js';

beforeEach(() => {
  store.clear();
  process.env.NODE_ENV = 'test';
});

describe('POST /transactions', () => {
  it('creates a valid deposit (201)', async () => {
    const res = await request(app)
      .post('/transactions')
      .send({ type: 'deposit', toAccount: 'ACC-11111', amount: 100, currency: 'USD' });

    expect(res.status).toBe(201);
    expect(res.body).toMatchObject({
      type: 'deposit',
      toAccount: 'ACC-11111',
      amount: 100,
      currency: 'USD',
      status: 'completed',
    });
    expect(res.body.id).toBeDefined();
    expect(res.body.timestamp).toBeDefined();
  });

  it('creates a valid transfer (201)', async () => {
    const res = await request(app)
      .post('/transactions')
      .send({ type: 'transfer', fromAccount: 'ACC-11111', toAccount: 'ACC-22222', amount: 50.99, currency: 'EUR' });

    expect(res.status).toBe(201);
    expect(res.body.amount).toBe(50.99);
    expect(res.body.fromAccount).toBe('ACC-11111');
    expect(res.body.toAccount).toBe('ACC-22222');
  });

  it('creates a valid withdrawal (201)', async () => {
    const res = await request(app)
      .post('/transactions')
      .send({ type: 'withdrawal', fromAccount: 'ACC-11111', amount: 25, currency: 'GBP' });

    expect(res.status).toBe(201);
    expect(res.body.type).toBe('withdrawal');
  });

  it('rejects negative amount (400)', async () => {
    const res = await request(app)
      .post('/transactions')
      .send({ type: 'deposit', toAccount: 'ACC-11111', amount: -50, currency: 'USD' });

    expect(res.status).toBe(400);
    expect(res.body.error).toBe('Validation failed');
    expect(Array.isArray(res.body.details)).toBe(true);
    expect(res.body.details.some((d: { field: string }) => d.field === 'amount')).toBe(true);
  });

  it('rejects invalid currency (400)', async () => {
    const res = await request(app)
      .post('/transactions')
      .send({ type: 'deposit', toAccount: 'ACC-11111', amount: 100, currency: 'XYZ' });

    expect(res.status).toBe(400);
    expect(res.body.details.some((d: { field: string }) => d.field === 'currency')).toBe(true);
  });

  it('rejects bad account format (400)', async () => {
    const res = await request(app)
      .post('/transactions')
      .send({ type: 'deposit', toAccount: 'INVALID', amount: 100, currency: 'USD' });

    expect(res.status).toBe(400);
    expect(res.body.details.some((d: { field: string }) => d.field === 'toAccount')).toBe(true);
  });

  it('ignores extra fields in request body', async () => {
    const res = await request(app)
      .post('/transactions')
      .send({ type: 'deposit', toAccount: 'ACC-11111', amount: 100, currency: 'USD', extraField: 'ignored' });

    expect(res.status).toBe(201);
    expect((res.body as Record<string, unknown>).extraField).toBeUndefined();
  });
});

describe('GET /transactions', () => {
  beforeEach(async () => {
    await request(app).post('/transactions').send({ type: 'deposit', toAccount: 'ACC-11111', amount: 100, currency: 'USD' });
    await request(app).post('/transactions').send({ type: 'withdrawal', fromAccount: 'ACC-11111', amount: 30, currency: 'USD' });
    await request(app).post('/transactions').send({ type: 'transfer', fromAccount: 'ACC-11111', toAccount: 'ACC-22222', amount: 50, currency: 'EUR' });
  });

  it('returns all transactions (200)', async () => {
    const res = await request(app).get('/transactions');
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(3);
  });

  it('returns empty array when store is empty (200)', async () => {
    store.clear();
    const res = await request(app).get('/transactions');
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(0);
  });

  it('filters by accountId', async () => {
    const res = await request(app).get('/transactions?accountId=ACC-22222');
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(1);
    expect((res.body[0] as { type: string }).type).toBe('transfer');
  });

  it('filters by type=transfer', async () => {
    const res = await request(app).get('/transactions?type=transfer');
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(1);
    expect((res.body[0] as { type: string }).type).toBe('transfer');
  });

  it('filters by type=withdrawal', async () => {
    const res = await request(app).get('/transactions?type=withdrawal');
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(1);
  });

  it('combines accountId and type filters', async () => {
    const res = await request(app).get('/transactions?accountId=ACC-11111&type=transfer');
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(1);
  });

  it('returns empty when combined filters match nothing', async () => {
    const res = await request(app).get('/transactions?accountId=ACC-99999&type=deposit');
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(0);
  });

  it('filters by date range (past dates return empty)', async () => {
    const res = await request(app).get('/transactions?from=2000-01-01&to=2000-12-31');
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(0);
  });
});

describe('GET /transactions/:id', () => {
  it('returns a transaction by id (200)', async () => {
    const createRes = await request(app)
      .post('/transactions')
      .send({ type: 'deposit', toAccount: 'ACC-11111', amount: 100, currency: 'USD' });

    const id = (createRes.body as { id: string }).id;
    const res = await request(app).get(`/transactions/${id}`);

    expect(res.status).toBe(200);
    expect((res.body as { id: string }).id).toBe(id);
  });

  it('returns 404 for unknown id', async () => {
    const res = await request(app).get('/transactions/non-existent-id');
    expect(res.status).toBe(404);
    expect((res.body as { error: string }).error).toBeDefined();
  });
});
