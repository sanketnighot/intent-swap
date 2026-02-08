# IntentSwap

IntentSwap is an agent-driven execution layer for Uniswap v4.

Users submit conditional swap intents instead of executing swaps immediately. An offchain execution agent monitors onchain state and submits swaps only when intent conditions are satisfied. A Uniswap v4 hook enforces all conditions onchain at `beforeSwap`, so invalid execution attempts revert.

## Judge-Friendly Summary

IntentSwap demonstrates agentic infrastructure, not speculative intelligence.

- The agent is autonomous: it runs continuously, observes pool and intent state, and submits transactions without manual triggers.
- The agent is constrained: it cannot bypass policy because the hook validates execution conditions onchain.
- The design is composable: anyone can run an executor; correctness does not depend on one privileged bot.

## Alignment With Uniswap v4 Agentic Finance

| Requirement theme | IntentSwap implementation |
| --- | --- |
| Agent-driven system | Python executor continuously checks and executes valid intents |
| Programmatic interaction with v4 pools | Agent calls swap entrypoint with `PoolKey`, `SwapParams`, and `hookData` |
| Reliability | Hook revalidates all conditions in `beforeSwap`; invalid attempts revert |
| Transparency | Intents are explicit onchain state (`amountIn`, condition, expiry, executed) |
| Composability | Any actor can execute intents; hook remains source of truth |
| Non-speculative intelligence | No prediction, no ML, no strategy optimization |
| Hooks used meaningfully | `IntentSwapHook` is the execution policy engine |

## What The Agent Is (And Is Not)

The IntentSwap agent **is** an execution coordinator:

- observes onchain state
- evaluates deterministic execution rules
- submits execution transactions

The IntentSwap agent **is not**:

- a price prediction model
- a custody layer
- a discretionary trading strategy

## Architecture

```text
User
  -> submitIntent(...)
IntentSwapHook (onchain intent registry + policy)
  -> Intent stored
Execution Agent (offchain loop)
  -> reads intent + pool state
  -> calls canExecuteIntent(...)
  -> submits swap(..., hookData=intentId)
IntentSwapHook.beforeSwap(...)
  -> validates intent constraints
  -> marks executed OR reverts
```

## Core Runtime Components

```text
/
├── contracts/
│   └── IntentSwapHook.sol
├── agent/
│   └── executor.py
├── scripts/
│   └── deploy.js
├── .env.example
├── package.json
└── pyproject.toml
```

### Onchain: `contracts/IntentSwapHook.sol`

Primary source of execution correctness.

- Stores swap intents onchain (`submitIntent`)
- Validates execution in `_beforeSwap`
- Reverts when intent is expired, already executed, mismatched, or price condition fails
- Marks intent as executed only after successful validation

Intent fields:

- `user`
- `tokenIn`
- `tokenOut`
- `amountIn`
- `conditionType` (`TARGET_SQRT_PRICE_X96` or `MAX_SLIPPAGE_BPS`)
- `conditionValue`
- `expiry`
- `executed`
- `poolId`
- `zeroForOne`
- `referenceSqrtPriceX96`

### Offchain: `agent/executor.py`

Deterministic, rule-based execution loop.

- Polls `intentCount` and each intent
- Skips intents already executed or expired
- Calls `canExecuteIntent(...)`
- Submits `swap(...)` with `hookData = abi.encode(intentId)` (32-byte encoded intent id)

The offchain agent cannot force invalid execution; hook checks are final.

## Why This Is Agentic Infrastructure

IntentSwap separates:

- decision timing (offchain agent)
- execution trigger (submitted transaction)
- enforcement (onchain hook)

This makes the system robust to agent replacement and aligned with protocol-level guarantees.

## Assumptions

- Uniswap v4 dependencies are available in Solidity toolchain:
  - `@uniswap/v4-core`
  - `@uniswap/v4-periphery`
- A swap entrypoint exists at `SWAP_TARGET_ADDRESS` with:
  - `swap(PoolKey key, SwapParams params, bytes hookData)`
- Contract artifact exists before deploy:
  - `artifacts/contracts/IntentSwapHook.sol/IntentSwapHook.json`

## Setup

1. Install JS dependencies:

```bash
npm install
```

2. Install Python dependencies with `uv`:

```bash
uv sync
```

3. Create env file:

```bash
cp .env.example .env
```

4. Compile Solidity contract using your toolchain (artifact required by deploy script).

5. Deploy hook:

```bash
npm run deploy
```

6. Start execution agent:

```bash
uv run python -m agent.cli.main agent run
```

## Environment Variables

See `.env.example`:

- `RPC_URL`
- `PRIVATE_KEY`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GEMINI_TIMEOUT_MS`
- `POOL_MANAGER_ADDRESS`
- `HOOK_ADDRESS`
- `SWAP_TARGET_ADDRESS`
- `POOL_CURRENCY0`
- `POOL_CURRENCY1`
- `POOL_FEE`
- `POOL_TICK_SPACING`
- `POLL_INTERVAL_MS`
- `RPC_TIMEOUT_SEC`
- `RECEIPT_TIMEOUT_SEC`
- `EXECUTOR_RETRY_ATTEMPTS`
- `EXECUTOR_RETRY_DELAY_MS`
- `EXECUTOR_INFLIGHT_TTL_SEC`
- `EXECUTOR_STATE_FILE`

## CLI

Full command reference is in `docs/cli-reference.md`.

Run help:

```bash
uv run python -m agent.cli.main --help
```

Validate config:

```bash
uv run python -m agent.cli.main config validate
uv run python -m agent.cli.main config validate --profile deploy
uv run python -m agent.cli.main config validate --profile gemini
```

JSON output:

```bash
uv run python -m agent.cli.main --json config validate
```

Dry-run examples for tx-producing commands:

```bash
uv run python -m agent.cli.main intent execute --id 0 --dry-run
uv run python -m agent.cli.main intent create --text "swap 1 ETH to USDC when condition is met" --dry-run
```

Intent inspection and execution commands:

```bash
uv run python -m agent.cli.main intent list
uv run python -m agent.cli.main intent show --id 0
uv run python -m agent.cli.main intent can-execute --id 0
uv run python -m agent.cli.main intent execute --id 0
uv run python -m agent.cli.main intent create --json-file intent.json
uv run python -m agent.cli.main intent create --text "Swap 1000000 units of token0 to token1 when slippage <= 100 bps before 1735689600"
uv run python -m agent.cli.main agent run --interval-ms 5000
uv run python -m agent.cli.main agent run-once
uv run python -m agent.cli.main agent run-once --dry-run
```

`agent run` and `agent run-once` emit structured JSON event lines with reason codes such as:

- `SKIP_EXECUTED`
- `SKIP_EXPIRED`
- `SKIP_NOT_EXECUTABLE`
- `SKIP_INFLIGHT`
- `EXECUTE_SUBMITTED`
- `EXECUTE_CONFIRMED`
- `EXECUTE_REVERTED`

Example `intent.json` payload:

```json
{
  "token_in": "0x0000000000000000000000000000000000000001",
  "token_out": "0x0000000000000000000000000000000000000002",
  "amount_in": 1000000,
  "condition_type": "MAX_SLIPPAGE_BPS",
  "condition_value": 100,
  "expiry": 1893456000
}
```

Run current Python unit tests:

```bash
python3 -m unittest discover -s tests -v
```

Contract guard assertions are included in:

- `tests/test_contract_guards.py`

## Coding Agent Setup

This repository includes cross-agent instruction files:

- `AGENTS.md` (canonical rules)
- `CLAUDE.md` (Claude Code)
- `CODEX.md` (Codex)
- `.cursor/rules/intentswap-core.mdc` and `.cursorrules` (Cursor)
- `.github/copilot-instructions.md` (Copilot)
- `skills/` (repo-local reusable skills)
- `docs/agent-index.md` (quick index)

## Submission Evidence Checklist

For hackathon submission completeness:

- Use `docs/evidence-checklist.md` and fill all tx-id fields.
- Keep this README, `docs/cli-reference.md`, and `docs/demo-script.md` aligned.
- Provide demo video (<= 3 min) showing:
  - intent creation
  - agent detection/execution pass
  - execution tx confirmation
  - hook enforcement behavior
