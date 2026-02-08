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

2. `agent/executor.py`
- Polls intent state.
- Filters non-executable intents.
- Calls `canExecuteIntent(...)`.
- Submits execution transaction with encoded intent id.

3. `scripts/deploy.js`
- Deploys hook from compiled artifact.

## Execution Flow

1. User submits intent onchain.
2. Agent reads current intents and pool state.
3. Agent checks if an intent is executable now.
4. Agent submits swap call with `hookData = abi.encode(intentId)`.
5. Hook revalidates all constraints in `beforeSwap`.
6. Swap executes or reverts.

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
