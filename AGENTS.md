# IntentSwap Agent Contract

This file defines project rules for autonomous coding agents (Codex, Claude Code, Cursor, Copilot, and similar tools).

## Project Scope

IntentSwap is an intent-based swap execution system on Uniswap v4.

- Users submit swap intents with explicit execution conditions.
- Offchain agents coordinate execution timing.
- Onchain hook logic enforces correctness and safety.

## Hard Invariants

1. Hook validation is the source of truth.
2. Offchain agents are coordinators, not authorities.
3. No custody of user funds.
4. No predictive AI, ML signals, or speculative strategy logic.
5. Keep execution deterministic and explainable.

## Architecture Anchors

- Onchain policy + intent storage: `contracts/IntentSwapHook.sol`
- Offchain execution loop: `agent/executor.py`
- Deploy helper: `scripts/deploy.js`

## Non-Goals

- No UI/frontend work unless explicitly requested.
- No multi-chain expansion unless explicitly requested.
- No strategy optimization engine.

## Coding Rules

1. Do not add features that were not requested.
2. Prefer explicit logic over abstractions.
3. Keep files small and readable.
4. Preserve line-by-line explainability.
5. Do not frame components as a trading bot.
6. Document assumptions when external dependencies or environment details are required.

## Agent Workflow

1. Read `README.md` and `docs/architecture.md` before major changes.
2. Confirm requested scope and list assumptions.
3. Implement minimal changes that satisfy the request.
4. Run relevant checks (lint/tests/compile or syntax checks).
5. Update docs when behavior, interfaces, or run commands change.
6. Summarize changes with file paths and any gaps.

## Validation Expectations

- Contract changes: include compile/test instructions or test updates.
- Agent changes: include runtime/syntax checks and error-path handling.
- Do not claim successful tests you did not run.

## LLM Provider Policy

- LLMs may assist with parsing or operator UX only.
- LLM output must be validated before any transaction execution path.
- Final execution permission must remain onchain via hook checks.

## Local Skills

Repo-local skills are in `skills/`:

- `skills/intentswap-engineering/`
- `skills/intentswap-submission/`

Use them for repeated, structured tasks.
