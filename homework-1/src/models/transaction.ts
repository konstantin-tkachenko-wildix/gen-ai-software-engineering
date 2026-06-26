import { v4 as uuidv4 } from 'uuid';
import type { Transaction, CreateTransactionDto } from '../types/index.js';

export function createTransaction(dto: CreateTransactionDto): Transaction {
  return {
    id: uuidv4(),
    fromAccount: dto.fromAccount ?? null,
    toAccount: dto.toAccount ?? null,
    amount: dto.amount,
    currency: dto.currency.toUpperCase(),
    type: dto.type,
    timestamp: new Date().toISOString(),
    status: 'completed',
  };
}
