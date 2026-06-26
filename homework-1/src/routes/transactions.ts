import { Router } from 'express';
import type { Request, Response } from 'express';
import { validate } from '../validators/transactionValidator.js';
import { createTransaction } from '../models/transaction.js';
import { store } from '../store/transactionStore.js';
import type { TransactionFilter, TransactionType } from '../types/index.js';

const router = Router();

router.post('/transactions', (req: Request, res: Response) => {
  const result = validate(req.body as Record<string, unknown>);
  if (!result.valid) {
    res.status(400).json({ error: 'Validation failed', details: result.errors });
    return;
  }
  const tx = createTransaction(req.body);
  store.add(tx);
  res.status(201).json(tx);
});

router.get('/transactions', (req: Request, res: Response) => {
  const filter: TransactionFilter = {};
  if (typeof req.query.accountId === 'string') filter.accountId = req.query.accountId;
  if (typeof req.query.type === 'string') filter.type = req.query.type as TransactionType;
  if (typeof req.query.from === 'string') filter.from = req.query.from;
  if (typeof req.query.to === 'string') filter.to = req.query.to;
  res.json(store.filter(filter));
});

router.get('/transactions/:id', (req: Request, res: Response) => {
  const tx = store.getById(req.params.id);
  if (!tx) {
    res.status(404).json({ error: 'Transaction not found' });
    return;
  }
  res.json(tx);
});

export { router as transactionsRouter };
