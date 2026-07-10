# Homework 3 — Virtual Payment Card Specification

## Student & Task Summary

**Student:** Kostiantyn Tkachenko

**Homework:** Specification-Driven Design

**AI Tools Used:** Cursor with Claude Sonnet 5 and Gemini 3.1 Pro.

**Deliverable summary:** A layered specification for **personal virtual payment card lifecycle management**—covering create, activate, freeze/unfreeze, spending limits, transactions, close, rename, notifications, PIN, reissue, expiration, dispute intake, and ops/compliance audit—plus supporting Cursor rules. No implementation code is included; the graded artifact is the specification itself.

**Files in this submission:**


| File                                  | Purpose                                      |
| ------------------------------------- | -------------------------------------------- |
| `specification.md`                    | Full feature specification                   |
| `AGENTS.md`                           | AI agent guidelines (FinTech Go conventions) |
| `.cursor/rules/virtual-card-spec.mdc` | Cursor rules for spec work in this folder    |


---



## Rationale



### Scope choices


| Decision                                                    | Rationale                                                                                                                                                                         |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Personal user only**                                      | Avoids org-admin RBAC, employee sub-users, and spend-policy inheritance—keeps the spec focused while still including an ops/compliance stakeholder via fraud hold and audit APIs. |
| **Wallet-funded (prepaid/debit)**                           | Simplest funding model; limits and declines reconcile directly against an internal balance without credit-line interest, statements, or external bank ACH complexity.             |
| **Distinct** `FROZEN_USER` **vs** `FROZEN_FRAUD` **states** | Prevents ambiguous “frozen” status where a user might self-unfreeze during an active fraud investigation—a common production requirement on issuing platforms.                    |
| **Explicit activation step**                                | Industry pattern (Stripe Issuing, Marqeta) reduces accidental use of newly issued credentials and creates a clear audit checkpoint before first spend.                            |
| **Close vs hard delete**                                    | Soft-close preserves transaction history and satisfies ledger immutability (`AGENTS.md`); aligns with regulatory retention expectations.                                          |




### Layering approach

The spec follows the required table in `TASKS.md`:

1. **High-level objective** — single north-star sentence with explicit scope boundary.
2. **Mid-level objectives (MO-1 … MO-15)** — each is observable and testable; maps to task groups A–I.
3. **Non-functional & policy** — security, privacy, audit, reliability, and performance summary before implementation details.
4. **Implementation notes** — concrete guardrails (decimal money, UTC, ID formats, error taxonomy, idempotency) so an AI agent or engineer does not guess.
5. **Context** — hypothetical beginning/ending workspace to anchor what exists before vs after build.
6. **Low-level tasks (40 tasks)** — small, grouped slices with acceptance criteria on critical paths.
7. **Cross-cutting sections** — edge cases, verification matrix, and performance targets integrated into the spec body, not relegated to README.



### Performance target choices

All targets in `specification.md : Expected Performance` are labeled **assumed** because no production traffic data exists. They were chosen as follows:

- **Sub-second create/activate/freeze** — consumer mobile apps treat card controls as instant; p95 < 1s is a common issuing-API UX bar.
- **2s freeze propagation** — balances cache replication latency with fraud-response expectations when a user reports a stolen device.
- **500ms transaction list** — standard paginated feed SLO for 50 rows with indexed queries.
- **5s notification dispatch** — near-real-time awareness without blocking the authorization path (async outbox).
- **Rate limits (reveal, create, PIN lockout)** — reduce PAN exposure and abuse; aligned with PCI assessor expectations for sensitive operations.



### Verification depth

Verification is documented as **test categories and fixtures**, not executable tests (homework constraint). Each mid-level objective maps to unit, integration, e2e, or reconciliation methods in `specification.md : Verification`. Nightly limit-counter reconciliation and audit immutability review reflect ops/compliance needs beyond happy-path e2e.

---



### Practices intentionally out of scope

Documented in `specification.md : Out of Scope`: wallet tokenization, business cards, physical cards, FX, and full dispute resolution—these would expand PCI, scheme certification, and legal scope beyond a homework specification.

---



## How to use this package

1. Read `specification.md` top-down: objectives → policy → tasks.
2. When implementing (future homework or production), follow `AGENTS.md` for Go/FinTech code generation.
3. Cursor will apply `.cursor/rules/virtual-card-spec.mdc` when editing files under `homework-3/`.

