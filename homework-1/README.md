# Banking Transactions API

> **Student Name**: Konstantin Tkachenko
> **Date Submitted**: 2026-06-26
> **AI Tools Used**: Claude Code (claude-sonnet-4-6)

---

## Project Overview

A minimal REST API for banking transactions built with **Node.js**, **Express**, and **TypeScript** (ESM). The API supports deposits, withdrawals, and transfers with in-memory storage, full input validation, transaction filtering, account balance/summary endpoints, and rate limiting.

---

## Features Implemented

| Task | Status |
|------|--------|
| Core CRUD endpoints (POST/GET transactions, GET by ID) | Done |
| Account balance endpoint | Done |
| Input validation (amount, account format, currency) | Done |
| Transaction filtering (by account, type, date range) | Done |
| **Option A** — Account summary endpoint | Done |
| **Option D** — Rate limiting (100 req/min/IP) | Done |

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/transactions` | Create a transaction |
| `GET` | `/transactions` | List all (with filters) |
| `GET` | `/transactions/:id` | Get by ID |
| `GET` | `/accounts/:accountId/balance` | Get account balance |
| `GET` | `/accounts/:accountId/summary` | Get account summary |

### Query parameters for `GET /transactions`

| Param | Example | Description |
|-------|---------|-------------|
| `accountId` | `ACC-12345` | Filter by from/to account |
| `type` | `transfer` | Filter by type |
| `from` | `2024-01-01` | Start date (inclusive) |
| `to` | `2024-01-31` | End date (inclusive) |

---

## Transaction Model

```json
{
  "id": "uuid (auto-generated)",
  "fromAccount": "ACC-XXXXX or null",
  "toAccount": "ACC-XXXXX or null",
  "amount": 100.50,
  "currency": "USD",
  "type": "deposit | withdrawal | transfer",
  "timestamp": "ISO 8601",
  "status": "completed"
}
```

---

## Architecture

```
src/
├── app.ts              Express app factory (no listen)
├── server.ts           Entry point — calls app.listen()
├── types/index.ts      TypeScript interfaces
├── store/              In-memory singleton store
├── models/             Transaction factory
├── validators/         Input validation logic
├── routes/             Express routers
├── middleware/         Rate limiter, error handler
└── utils/              ISO 4217 currency codes
```

**Key decisions:**
- `app.ts` exports the Express app without calling `listen()`, enabling clean supertest integration
- Balance is computed on-demand by scanning completed transactions (no derived state stored)
- `fromAccount` is optional for deposits; `toAccount` is optional for withdrawals; both required for transfers
- All transactions are created with `status: 'completed'` immediately (no async pipeline to simulate)
- When an account has transactions in multiple currencies, the balance endpoint returns `"currency": "MIXED"`

---

## Known Limitations

- **In-memory storage**: all data is lost on server restart
- **Multi-currency balance**: the balance endpoint sums amounts across all currencies and reports `"currency": "MIXED"` when multiple currencies are present. Artificially limiting accounts to a single currency or introducing hardcoded currency conversion rates were both intentionally avoided as they add constraints without real value in an in-memory demo context
- **Status field**: `pending` and `failed` statuses exist in the type definition but are never assigned (no async processing)

---

<div align="center">

*This project was completed as part of the AI-Assisted Development course.*

</div>
