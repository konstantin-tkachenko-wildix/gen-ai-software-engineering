import { Router } from 'express';
import { transactionsRouter } from './transactions.js';
import { accountsRouter } from './accounts.js';

const router = Router();

router.use('/', transactionsRouter);
router.use('/', accountsRouter);

export { router };
