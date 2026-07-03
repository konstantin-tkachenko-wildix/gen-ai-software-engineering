import { Router } from 'express';
import type { Request, Response } from 'express';
import { store } from '../store/transactionStore.js';
import type { Transaction } from '../types/index.js';

const router = Router();

function getAccountTransactions(accountId: string): Transaction[] {
  return store
    .getAll()
    .filter((tx) => tx.status === 'completed' && (tx.fromAccount === accountId || tx.toAccount === accountId));
}

router.get('/accounts/:accountId/balance', (req: Request, res: Response) => {
  const { accountId } = req.params;
  const txs = getAccountTransactions(accountId);

  if (txs.length === 0) {
    res.status(404).json({ error: 'Account not found' });
    return;
  }

  let balance = 0;
  const currencies = new Set<string>();

  for (const tx of txs) {
    currencies.add(tx.currency);
    if (tx.type === 'deposit' && tx.toAccount === accountId) {
      balance += tx.amount;
    } else if (tx.type === 'withdrawal' && tx.fromAccount === accountId) {
      balance -= tx.amount;
    } else if (tx.type === 'transfer') {
      if (tx.toAccount === accountId) balance += tx.amount;
      if (tx.fromAccount === accountId) balance -= tx.amount;
    }
  }

  res.json({
    accountId,
    balance: Math.round(balance * 100) / 100,
    currency: currencies.size === 1 ? [...currencies][0] : 'MIXED',
  });
});

router.get('/accounts/:accountId/summary', (req: Request, res: Response) => {
  const { accountId } = req.params;
  const txs = getAccountTransactions(accountId);

  if (txs.length === 0) {
    res.status(404).json({ error: 'Account not found' });
    return;
  }

  let totalDeposits = 0;
  let totalWithdrawals = 0;
  let mostRecentDate = txs[0].timestamp;

  for (const tx of txs) {
    if (tx.timestamp > mostRecentDate) mostRecentDate = tx.timestamp;

    if (tx.type === 'deposit' && tx.toAccount === accountId) {
      totalDeposits += tx.amount;
    } else if (tx.type === 'withdrawal' && tx.fromAccount === accountId) {
      totalWithdrawals += tx.amount;
    } else if (tx.type === 'transfer') {
      if (tx.toAccount === accountId) totalDeposits += tx.amount;
      if (tx.fromAccount === accountId) totalWithdrawals += tx.amount;
    }
  }

  res.json({
    accountId,
    totalDeposits: Math.round(totalDeposits * 100) / 100,
    totalWithdrawals: Math.round(totalWithdrawals * 100) / 100,
    transactionCount: txs.length,
    mostRecentDate,
  });
});

export { router as accountsRouter };
