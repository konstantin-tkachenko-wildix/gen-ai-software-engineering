export type TransactionType = 'deposit' | 'withdrawal' | 'transfer';
export type TransactionStatus = 'pending' | 'completed' | 'failed';

export interface Transaction {
  id: string;
  fromAccount: string | null;
  toAccount: string | null;
  amount: number;
  currency: string;
  type: TransactionType;
  timestamp: string;
  status: TransactionStatus;
}

export interface CreateTransactionDto {
  fromAccount?: string | null;
  toAccount?: string | null;
  amount: number;
  currency: string;
  type: TransactionType;
}

export interface ValidationErrorDetail {
  field: string;
  message: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationErrorDetail[];
}

export interface TransactionFilter {
  accountId?: string;
  type?: TransactionType;
  from?: string;
  to?: string;
}
