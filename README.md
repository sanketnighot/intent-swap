# IntentSwap

IntentSwap is a minimal intent-based swap execution system for Uniswap v4.

Users submit swap intents with explicit execution conditions.  
An offchain agent monitors intents and submits swap transactions only when they are executable.  
The onchain hook enforces correctness in `beforeSwap` so invalid executions revert.

## Repository Structure

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

## Intent Model

Each intent stores:

- `user`
- `tokenIn`
- `tokenOut`
- `amountIn`
- execution condition: `TARGET_SQRT_PRICE_X96` or `MAX_SLIPPAGE_BPS`
- `expiry` timestamp
- `executed` flag

The hook also stores:

- `poolId`
- `zeroForOne` direction
- `referenceSqrtPriceX96` (captured on intent creation)

## Onchain Enforcement (Hook)

`contracts/IntentSwapHook.sol` is the primary correctness layer.

What it does:

- stores intents onchain with `submitIntent(...)`
- validates swaps in `_beforeSwap(...)` using the intent id from `hookData`
- reverts if intent does not exist
- reverts if intent is expired
- reverts if intent is already executed
- reverts if pool, direction, token pair, or amount does not match
- reverts if price condition is not satisfied
- marks intent as executed once validation passes

Execution is therefore deterministic and enforced onchain.

## Agent Role

`agent/executor.py` is a simple polling script.

What it does:

- reads `intentCount` and each stored intent
- skips expired or already executed intents
- checks `canExecuteIntent(...)`
- submits `swap(...)` with `hookData = abi.encode(intentId)` when executable

What it does not do:

- custody funds
- bypass hook checks
- make probabilistic strategy decisions

## Assumptions

- Solidity imports target official Uniswap v4 packages (`@uniswap/v4-core`, `@uniswap/v4-periphery`).
- A compatible swap entrypoint exists at `SWAP_TARGET_ADDRESS` exposing `swap(PoolKey key, SwapParams params, bytes hookData)`.
- Contract artifacts are generated before deploy (the deploy script reads `artifacts/contracts/IntentSwapHook.sol/IntentSwapHook.json`).

## Run

1. Install dependencies:

```bash
npm install
uv sync
```

2. Compile `contracts/IntentSwapHook.sol` with your Solidity toolchain so artifacts are generated.

3. Configure environment:

```bash
cp .env.example .env
```

4. Deploy hook:

```bash
npm run deploy
```

5. Start execution agent:

```bash
uv run python agent/executor.py
```
