# Homework 3: Virtual Payment Card Lifecycle Specification

## 📋 Summary

Layered **specification-only** deliverable for personal virtual payment card lifecycle management (wallet-funded prepaid/debit). Covers create, activate, freeze/unfreeze, spending limits, transactions, close, rename, notifications, PIN, reissue, expiration, dispute intake, and ops/compliance audit — with 15 mid-level objectives, 40 low-level tasks, a card state machine, 17 edge cases, verification matrix, and assumed performance SLOs. Supporting docs: `AGENTS.md` (FinTech Go agent rules) and `.cursor/rules/virtual-card-spec.mdc`. No implementation code.

## ✅ Tasks Completed

- ✅ **`specification.md`** — full layered spec (objectives → policy → implementation notes → context → tasks → edge cases → verification → performance)
- ✅ **`AGENTS.md`** — AI agent guidelines for regulated FinTech Go (decimal money, audit immutability, zero-trust logging)
- ✅ **Cursor rules** — `.cursor/rules/virtual-card-spec.mdc` (domain naming, PCI-safe examples, spec-only scope)
- ✅ **`README.md`** — rationale, scope decisions, industry-practice mapping with section references

## 🤖 AI Tools Used — Cursor (Claude Sonnet 5, Gemini 3.1 Pro)

- **Planning**: scoped persona (personal user), funding model (wallet balance), and feature set via structured clarifying questions before writing the spec
- **Specification drafting**: agent produced layered `specification.md` from plan — state machine, task decomposition, edge-case table, verification matrix
- **Supporting docs**: README rationale and Cursor rule file generated to match TASKS.md deliverables
- Verified myself: read-through for traceability (user feature → MO → task group), checked all TASKS.md cross-cutting requirements are in the spec body (not README-only), confirmed screenshots capture the AI workflow

## ⚠️ Challenges Encountered & How They Were Addressed

**Scope creep vs homework boundary** — virtual cards invite tokenization, business cards, and FX; explicitly documented out-of-scope items and kept wallet-funded personal use only.

**User freeze vs fraud hold ambiguity** — single `FROZEN` status would let users self-unfreeze during investigations; split into `FROZEN_USER` and `FROZEN_FRAUD` with distinct transitions and ops-only release.

**Spec-only verification** — no runnable app or tests; documented verification as test categories, fixtures, and reconciliation checks an implementer would run later, per homework constraint.

## ▶️ How to Verify

Homework 3 is documentation only — no install or test suite. Review the submission as follows:

```bash
cd homework-3

# Core deliverables present
dir specification.md AGENTS.md README.md .cursor\rules\virtual-card-spec.mdc

# Read top-down: objectives → tasks → edge cases
# specification.md — check MO-1..MO-15 trace to task groups A–I
# README.md — rationale and industry-practice table with section refs
# AGENTS.md — FinTech guardrails align with spec Implementation Notes
```

Confirm `specification.md` includes integrated **edge cases**, **verification**, and **expected performance** sections (not relegated to README alone), per `TASKS.md`.

## 📸 Screenshots

**AI workflow:**

![Initial feature planning and scope questions](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-3-submission/homework-3/docs/screenshots/prompt-1.png)

![Specification structure and layering discussion](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-3-submission/homework-3/docs/screenshots/prompt-2.png)

![Review and refinement of virtual card lifecycle spec](https://raw.githubusercontent.com/konstantin-tkachenko-wildix/gen-ai-software-engineering/homework-3-submission/homework-3/docs/screenshots/prompt-3.png)

## 💡 Key Architecture Decisions

- **Wallet-funded prepaid/debit** — simplest funding model; limits reconcile against internal balance without credit-line complexity
- **Distinct `FROZEN_USER` / `FROZEN_FRAUD` states** — prevents user self-unfreeze during fraud investigations
- **Explicit activation (`PENDING_ACTIVATION` → `ACTIVE`)** — audit checkpoint before first spend; industry-consistent issuing pattern
- **Soft-close (`CLOSED`) not hard delete** — preserves transaction history and satisfies ledger immutability
- **PCI scope reduction in spec** — tokenized PAN in app DB, full PAN/CVV via rate-limited reveal only; never in logs
