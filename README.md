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

## Core Components

```text
/
├── contracts/
│   └── IntentSwapHook.sol
├── agent/
│   └── executor.py
├── scripts/
│   └── deploy.js
├── README.md
├── package.json
├── pyproject.toml
└── .env.example
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
uv run python agent/executor.py
```

## Environment Variables

See `.env.example`:

- `RPC_URL`
- `PRIVATE_KEY`
- `POOL_MANAGER_ADDRESS`
- `HOOK_ADDRESS`
- `SWAP_TARGET_ADDRESS`
- `POOL_CURRENCY0`
- `POOL_CURRENCY1`
- `POOL_FEE`
- `POOL_TICK_SPACING`
- `POLL_INTERVAL_MS`

## Submission Evidence Checklist

For hackathon submission completeness:

- Include deployment and execution transaction IDs
- Keep this README with architecture and run steps
- Provide demo video (<= 3 min) showing:
  - intent creation
  - agent detecting executable state
  - execution tx
  - successful hook enforcement
