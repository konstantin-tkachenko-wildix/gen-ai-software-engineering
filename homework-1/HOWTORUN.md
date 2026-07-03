# How to Run the Application

## Prerequisites

- **Node.js** v18 or later — [nodejs.org](https://nodejs.org)
- **npm** v8 or later (bundled with Node.js)

---

## 1. Install dependencies

```bash
cd homework-1
npm install
```

---

## 2. Start the server

```bash
npm start
```

The server starts on **http://localhost:3000** by default.
To use a different port: `PORT=4000 npm start`

---

## 3. Run tests

```bash
npm test
```

Runs all four test suites (validation unit tests, transaction integration tests, account integration tests, rate-limit tests) using Jest + supertest.

---

## 4. Build (optional)

```bash
npm run build
```

Compiles TypeScript to `dist/`. Run the compiled output with:
```bash
node dist/server.js
```

---

## 5. Try the API manually

### Option A — VS Code REST Client

1. Open `demo/sample-requests.http` in VS Code
2. Install the **REST Client** extension (`humao.rest-client`) if not installed
3. Click **Send Request** above any request block

### Option B — curl

```bash
# Create a deposit
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"type":"deposit","toAccount":"ACC-11111","amount":1000,"currency":"USD"}'

# List all transactions
curl http://localhost:3000/transactions

# Get account balance
curl http://localhost:3000/accounts/ACC-11111/balance
```

---

## 6. Import into Postman

1. Open Postman → **File > Import**
2. Select `docs/api/openapi.yaml`
3. Postman generates a collection with all 5 endpoints pre-configured
4. Set the base URL variable to `http://localhost:3000`
5. Run requests against the running server

---

## Project Structure

```
homework-1/
├── src/           TypeScript source
├── tests/         Jest test suites
├── docs/
│   ├── agent/
│   │   └── session.md    AI planning and generation session history
│   ├── api/
│   │   └── openapi.yaml    OpenAPI 3.0 spec (import into Postman)
│   └── screenshots/        API and AI tool screenshots
└── demo/
    ├── run.bat          Windows startup script
    ├── sample-requests.http   VS Code REST Client requests
    └── sample-data.json       Example transaction objects
```
