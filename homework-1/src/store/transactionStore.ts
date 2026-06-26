import type { Transaction, TransactionFilter } from '../types/index.js';

const transactions: Transaction[] = [];

export const store = {
  add(tx: Transaction): Transaction {
    transactions.push(tx);
    return tx;
  },

  getAll(): Transaction[] {
    return [...transactions];
  },

  getById(id: string): Transaction | null {
    return transactions.find((t) => t.id === id) ?? null;
  },

  filter({ accountId, type, from, to }: TransactionFilter = {}): Transaction[] {
    return transactions.filter((tx) => {
      if (accountId && tx.fromAccount !== accountId && tx.toAccount !== accountId) return false;
      if (type && tx.type !== type) return false;
      if (from && new Date(tx.timestamp) < new Date(from + 'T00:00:00.000Z')) return false;
      if (to && new Date(tx.timestamp) > new Date(to + 'T23:59:59.999Z')) return false;
      return true;
    });
  },

  clear(): void {
    transactions.length = 0;
  },
};
