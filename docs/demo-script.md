# IntentSwap Demo Script (1 Minute)

## 0-10s: Problem

"Normal swaps execute immediately. IntentSwap lets users post conditional intents and execute only when conditions are valid."

## 10-20s: Architecture

"The hook stores intents and enforces execution constraints. The offchain agent only coordinates transaction timing."

## 20-35s: Intent Creation

- Show a transaction creating an intent with:
  - token pair
  - amount
  - condition type/value
  - expiry

"This is now onchain state."

## 35-50s: Agent Execution

- Show `uv run python agent/executor.py`
- Show logs for:
  - non-executable state (skips)
  - executable state (submission)
  - confirmation receipt

## 50-60s: Enforcement and Close

"Execution correctness is enforced by `beforeSwap` in the hook. Any invalid attempt reverts, so no trust in the agent is required."
