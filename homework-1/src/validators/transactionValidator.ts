import { CURRENCY_CODES } from '../utils/currencyCodes.js';
import type { ValidationResult, ValidationErrorDetail, TransactionType } from '../types/index.js';

const VALID_TYPES: TransactionType[] = ['deposit', 'withdrawal', 'transfer'];
const ACCOUNT_PATTERN = /^ACC-[A-Z0-9]{1,10}$/i;

export function validate(body: Record<string, unknown>): ValidationResult {
  const errors: ValidationErrorDetail[] = [];

  // type
  if (!body.type) {
    errors.push({ field: 'type', message: 'Transaction type is required' });
  } else if (!VALID_TYPES.includes(body.type as TransactionType)) {
    errors.push({ field: 'type', message: 'Type must be one of: deposit, withdrawal, transfer' });
  }

  const type = body.type as TransactionType | undefined;

  // amount
  if (body.amount === undefined || body.amount === null) {
    errors.push({ field: 'amount', message: 'Amount is required' });
  } else if (typeof body.amount !== 'number' || isNaN(body.amount)) {
    errors.push({ field: 'amount', message: 'Amount must be a number' });
  } else if (body.amount <= 0) {
    errors.push({ field: 'amount', message: 'Amount must be a positive number' });
  } else if (Math.round(body.amount * 100) !== body.amount * 100) {
    errors.push({ field: 'amount', message: 'Amount must have at most 2 decimal places' });
  }

  // currency
  if (!body.currency) {
    errors.push({ field: 'currency', message: 'Currency is required' });
  } else if (
    typeof body.currency !== 'string' ||
    !CURRENCY_CODES.has((body.currency as string).toUpperCase())
  ) {
    errors.push({
      field: 'currency',
      message: 'Invalid currency code. Use a valid ISO 4217 code (e.g., USD, EUR, GBP)',
    });
  }

  // fromAccount
  if (type === 'transfer' || type === 'withdrawal') {
    if (!body.fromAccount) {
      errors.push({ field: 'fromAccount', message: `fromAccount is required for ${type} transactions` });
    } else if (typeof body.fromAccount !== 'string' || !ACCOUNT_PATTERN.test(body.fromAccount)) {
      errors.push({ field: 'fromAccount', message: 'Account number must follow format ACC-XXXXX (alphanumeric)' });
    }
  } else if (body.fromAccount && typeof body.fromAccount === 'string') {
    if (!ACCOUNT_PATTERN.test(body.fromAccount)) {
      errors.push({ field: 'fromAccount', message: 'Account number must follow format ACC-XXXXX (alphanumeric)' });
    }
  }

  // toAccount
  if (type === 'transfer' || type === 'deposit') {
    if (!body.toAccount) {
      errors.push({ field: 'toAccount', message: `toAccount is required for ${type} transactions` });
    } else if (typeof body.toAccount !== 'string' || !ACCOUNT_PATTERN.test(body.toAccount)) {
      errors.push({ field: 'toAccount', message: 'Account number must follow format ACC-XXXXX (alphanumeric)' });
    }
  } else if (body.toAccount && typeof body.toAccount === 'string') {
    if (!ACCOUNT_PATTERN.test(body.toAccount)) {
      errors.push({ field: 'toAccount', message: 'Account number must follow format ACC-XXXXX (alphanumeric)' });
    }
  }

  return { valid: errors.length === 0, errors };
}
