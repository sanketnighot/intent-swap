# IntentSwap Demo Script (1 Minute)

This script is aligned with current CLI commands.

## 0-10s: Problem

"Normal swaps execute immediately. IntentSwap lets users post conditional intents and execute only when conditions are valid."

## 10-20s: Architecture

"The hook stores intents and enforces execution constraints. The offchain agent only coordinates transaction timing."

## 20-35s: Intent Creation

- Show dry-run JSON intent parse/validation:

```bash
uv run python -m agent.cli.main --json intent create --json-file intent.json --dry-run
```

- Show real intent creation transaction:

```bash
uv run python -m agent.cli.main --json intent create --json-file intent.json
```

"This is now onchain state."

## 35-50s: Agent Execution

- Show one-pass dry-run:

```bash
uv run python -m agent.cli.main --json agent run-once --dry-run
```

- Show one-pass real execution:

```bash
uv run python -m agent.cli.main --json agent run-once
```

- Point out reason/event codes:
  - `SKIP_NOT_EXECUTABLE`
  - `EXECUTE_SUBMITTED`
  - `EXECUTE_CONFIRMED`
  - `PASS_SUMMARY`

## 50-60s: Enforcement and Close

"Execution correctness is enforced by `beforeSwap` in the hook. Any invalid attempt reverts, so no trust in the agent is required."
