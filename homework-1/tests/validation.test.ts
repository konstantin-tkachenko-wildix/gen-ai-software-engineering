import { validate } from '../src/validators/transactionValidator.js';

describe('Transaction Validator', () => {
  describe('valid inputs', () => {
    it('accepts a valid transfer', () => {
      const result = validate({
        type: 'transfer',
        fromAccount: 'ACC-11111',
        toAccount: 'ACC-22222',
        amount: 100.5,
        currency: 'USD',
      });
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('accepts a deposit without fromAccount', () => {
      const result = validate({ type: 'deposit', toAccount: 'ACC-11111', amount: 500, currency: 'EUR' });
      expect(result.valid).toBe(true);
    });

    it('accepts a withdrawal without toAccount', () => {
      const result = validate({ type: 'withdrawal', fromAccount: 'ACC-11111', amount: 50, currency: 'GBP' });
      expect(result.valid).toBe(true);
    });

    it('accepts amount with exactly 2 decimal places', () => {
      const result = validate({ type: 'deposit', toAccount: 'ACC-11111', amount: 100.99, currency: 'USD' });
      expect(result.valid).toBe(true);
    });
  });

  describe('amount validation', () => {
    it('rejects missing amount', () => {
      const result = validate({ type: 'deposit', toAccount: 'ACC-11111', currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'amount')).toBe(true);
    });

    it('rejects zero amount', () => {
      const result = validate({ type: 'deposit', toAccount: 'ACC-11111', amount: 0, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'amount')).toBe(true);
    });

    it('rejects negative amount', () => {
      const result = validate({ type: 'deposit', toAccount: 'ACC-11111', amount: -50, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'amount')).toBe(true);
    });

    it('rejects amount with 3 decimal places', () => {
      const result = validate({ type: 'deposit', toAccount: 'ACC-11111', amount: 100.999, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'amount')).toBe(true);
    });

    it('rejects non-numeric amount', () => {
      const result = validate({ type: 'deposit', toAccount: 'ACC-11111', amount: 'abc' as unknown as number, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'amount')).toBe(true);
    });
  });

  describe('type validation', () => {
    it('rejects missing type', () => {
      const result = validate({ toAccount: 'ACC-11111', amount: 100, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'type')).toBe(true);
    });

    it('rejects invalid type', () => {
      const result = validate({ type: 'wire', toAccount: 'ACC-11111', amount: 100, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'type')).toBe(true);
    });
  });

  describe('currency validation', () => {
    it('rejects missing currency', () => {
      const result = validate({ type: 'deposit', toAccount: 'ACC-11111', amount: 100 });
      expect(result.errors.some((e) => e.field === 'currency')).toBe(true);
    });

    it('rejects invalid currency code', () => {
      const result = validate({ type: 'deposit', toAccount: 'ACC-11111', amount: 100, currency: 'XYZ' });
      expect(result.errors.some((e) => e.field === 'currency')).toBe(true);
    });

    it('accepts valid ISO 4217 codes', () => {
      for (const code of ['USD', 'EUR', 'GBP', 'JPY']) {
        const result = validate({ type: 'deposit', toAccount: 'ACC-11111', amount: 100, currency: code });
        expect(result.errors.some((e) => e.field === 'currency')).toBe(false);
      }
    });
  });

  describe('account format validation', () => {
    it('rejects bad fromAccount format', () => {
      const result = validate({ type: 'transfer', fromAccount: '12345', toAccount: 'ACC-22222', amount: 100, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'fromAccount')).toBe(true);
    });

    it('rejects bad toAccount format', () => {
      const result = validate({ type: 'transfer', fromAccount: 'ACC-11111', toAccount: 'bad', amount: 100, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'toAccount')).toBe(true);
    });

    it('rejects missing fromAccount on transfer', () => {
      const result = validate({ type: 'transfer', toAccount: 'ACC-22222', amount: 100, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'fromAccount')).toBe(true);
    });

    it('rejects missing fromAccount on withdrawal', () => {
      const result = validate({ type: 'withdrawal', amount: 100, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'fromAccount')).toBe(true);
    });

    it('rejects missing toAccount on transfer', () => {
      const result = validate({ type: 'transfer', fromAccount: 'ACC-11111', amount: 100, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'toAccount')).toBe(true);
    });

    it('rejects missing toAccount on deposit', () => {
      const result = validate({ type: 'deposit', amount: 100, currency: 'USD' });
      expect(result.errors.some((e) => e.field === 'toAccount')).toBe(true);
    });

    it('returns multiple errors simultaneously', () => {
      const result = validate({ type: 'transfer', amount: -50, currency: 'XYZ' });
      expect(result.errors.length).toBeGreaterThan(2);
      expect(result.valid).toBe(false);
    });
  });
});
