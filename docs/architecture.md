# IntentSwap Architecture

## Purpose

IntentSwap separates swap intent declaration from swap execution time.

- Users define conditional intents.
- Offchain agents monitor state and attempt execution.
- Hook logic enforces conditions onchain.

## Components

1. `contracts/IntentSwapHook.sol`
- Stores intents.
- Validates execution in `beforeSwap`.
- Marks intent executed after successful validation.

2. `agent/execution_engine.py`
- Runs autonomous execution passes.
- Applies retry policy for onchain reads/submissions.
- Emits structured reason codes for every decision path.
- Reconciles in-flight transactions and prevents duplicate submissions.

3. `agent/state_store.py`
- Persists in-flight transaction state in a local JSON file.
- Enables restart-safe idempotent behavior.

4. `agent/cli/main.py`
- Provides CLI command groups: `intent`, `agent`, `config`.
- Supports `intent create --text` via Gemini parsing and strict local validation.
- Supports `intent create --json-file` for deterministic direct payload input.
- Supports `agent run` and `agent run-once`.

5. `scripts/deploy.js`
- Deploys hook from compiled artifact.

## Execution Flow

1. User submits intent onchain.
2. Agent reads current intents and pool state.
3. Agent checks if an intent is executable now.
4. Agent submits swap call with `hookData = abi.encode(intentId)`.
5. Hook revalidates all constraints in `beforeSwap`.
6. Swap executes or reverts.

For natural-language intent creation:

1. CLI receives text input.
2. Gemini returns structured intent JSON.
3. Local deterministic validator checks token pair, condition bounds, and expiry.
4. Hook `submitIntent(...)` stores the validated intent onchain.

## Intent Data Model

- `user`
- `tokenIn`
- `tokenOut`
- `amountIn`
- `conditionType`
- `conditionValue`
- `expiry`
- `executed`
- `poolId`
- `zeroForOne`
- `referenceSqrtPriceX96`

## Trust Model

- Offchain agent is untrusted and replaceable.
- Hook contract is the policy authority.
- Anyone may attempt execution; invalid attempts revert.

## Extension Points

- Add additional intent condition types if requested.
- Add alternative executors without changing trust model.
- Keep all enforcement onchain when extending features.
