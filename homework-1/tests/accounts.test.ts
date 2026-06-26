import request from 'supertest';
import { app } from '../src/app.js';
import { store } from '../src/store/transactionStore.js';

beforeEach(() => {
  store.clear();
  process.env.NODE_ENV = 'test';
});

async function post(body: object) {
  return request(app).post('/transactions').send(body);
}

describe('GET /accounts/:accountId/balance', () => {
  it('returns 404 for account with no transactions', async () => {
    const res = await request(app).get('/accounts/ACC-99999/balance');
    expect(res.status).toBe(404);
  });

  it('calculates balance after a deposit', async () => {
    await post({ type: 'deposit', toAccount: 'ACC-11111', amount: 500, currency: 'USD' });

    const res = await request(app).get('/accounts/ACC-11111/balance');
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ accountId: 'ACC-11111', balance: 500, currency: 'USD' });
  });

  it('calculates balance after deposit and withdrawal', async () => {
    await post({ type: 'deposit', toAccount: 'ACC-11111', amount: 500, currency: 'USD' });
    await post({ type: 'withdrawal', fromAccount: 'ACC-11111', amount: 150, currency: 'USD' });

    const res = await request(app).get('/accounts/ACC-11111/balance');
    expect(res.body.balance).toBe(350);
  });

  it('calculates balance as transfer receiver', async () => {
    await post({ type: 'transfer', fromAccount: 'ACC-11111', toAccount: 'ACC-22222', amount: 200, currency: 'USD' });

    const res = await request(app).get('/accounts/ACC-22222/balance');
    expect(res.body.balance).toBe(200);
  });

  it('calculates balance as transfer sender', async () => {
    await post({ type: 'deposit', toAccount: 'ACC-11111', amount: 500, currency: 'USD' });
    await post({ type: 'transfer', fromAccount: 'ACC-11111', toAccount: 'ACC-22222', amount: 200, currency: 'USD' });

    const res = await request(app).get('/accounts/ACC-11111/balance');
    expect(res.body.balance).toBe(300);
  });

  it('handles mixed transaction types correctly', async () => {
    await post({ type: 'deposit', toAccount: 'ACC-11111', amount: 1000, currency: 'USD' });
    await post({ type: 'withdrawal', fromAccount: 'ACC-11111', amount: 200, currency: 'USD' });
    await post({ type: 'transfer', fromAccount: 'ACC-11111', toAccount: 'ACC-22222', amount: 100, currency: 'USD' });
    await post({ type: 'transfer', fromAccount: 'ACC-33333', toAccount: 'ACC-11111', amount: 50, currency: 'USD' });

    // 1000 - 200 - 100 + 50 = 750
    const res = await request(app).get('/accounts/ACC-11111/balance');
    expect(res.body.balance).toBe(750);
  });

  it('reports MIXED currency when account has multi-currency transactions', async () => {
    await post({ type: 'deposit', toAccount: 'ACC-11111', amount: 100, currency: 'USD' });
    await post({ type: 'deposit', toAccount: 'ACC-11111', amount: 100, currency: 'EUR' });

    const res = await request(app).get('/accounts/ACC-11111/balance');
    expect(res.body.currency).toBe('MIXED');
  });
});

describe('GET /accounts/:accountId/summary', () => {
  it('returns 404 for account with no transactions', async () => {
    const res = await request(app).get('/accounts/ACC-99999/summary');
    expect(res.status).toBe(404);
  });

  it('returns correct summary for mixed transaction types', async () => {
    await post({ type: 'deposit', toAccount: 'ACC-11111', amount: 500, currency: 'USD' });
    await post({ type: 'withdrawal', fromAccount: 'ACC-11111', amount: 100, currency: 'USD' });
    await post({ type: 'transfer', fromAccount: 'ACC-11111', toAccount: 'ACC-22222', amount: 50, currency: 'USD' });

    const res = await request(app).get('/accounts/ACC-11111/summary');
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      accountId: 'ACC-11111',
      totalDeposits: 500,
      totalWithdrawals: 150, // 100 withdrawal + 50 outgoing transfer
      transactionCount: 3,
    });
    expect(res.body.mostRecentDate).toBeDefined();
  });

  it('counts incoming transfers as deposits in summary', async () => {
    await post({ type: 'transfer', fromAccount: 'ACC-33333', toAccount: 'ACC-11111', amount: 200, currency: 'USD' });

    const res = await request(app).get('/accounts/ACC-11111/summary');
    expect(res.body.totalDeposits).toBe(200);
    expect(res.body.totalWithdrawals).toBe(0);
    expect(res.body.transactionCount).toBe(1);
  });

  it('mostRecentDate reflects the latest transaction', async () => {
    await post({ type: 'deposit', toAccount: 'ACC-11111', amount: 100, currency: 'USD' });
    await new Promise((r) => setTimeout(r, 10)); // small delay to ensure different timestamps
    await post({ type: 'deposit', toAccount: 'ACC-11111', amount: 200, currency: 'USD' });

    const txs = store.getAll();
    const latestTimestamp = txs.reduce((a, b) => (a.timestamp > b.timestamp ? a : b)).timestamp;

    const res = await request(app).get('/accounts/ACC-11111/summary');
    expect(res.body.mostRecentDate).toBe(latestTimestamp);
  });
});
