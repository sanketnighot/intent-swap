# IntentSwap CLI Reference

This reference matches the current CLI implementation in `agent/cli/main.py`.

## Global

```bash
uv run python -m agent.cli.main [--json] [--dry-run] <group> <command> [options]
```

- `--json`: machine-readable output
- `--dry-run`: skip transaction submission for tx-producing commands

## Config Commands

### Validate Environment

```bash
uv run python -m agent.cli.main config validate
uv run python -m agent.cli.main config validate --profile agent
uv run python -m agent.cli.main config validate --profile deploy
uv run python -m agent.cli.main config validate --profile gemini
```

Profiles:

- `agent`: runtime agent execution env
- `deploy`: deploy script env
- `gemini`: Gemini parser env

## Intent Commands

### List Intents

```bash
uv run python -m agent.cli.main intent list
```

### Show Intent

```bash
uv run python -m agent.cli.main intent show --id 0
```

### Check Executability

```bash
uv run python -m agent.cli.main intent can-execute --id 0
```

### Execute Intent

```bash
uv run python -m agent.cli.main intent execute --id 0
uv run python -m agent.cli.main intent execute --id 0 --dry-run
```

### Create Intent from JSON

```bash
uv run python -m agent.cli.main intent create --json-file intent.json
uv run python -m agent.cli.main intent create --json-file intent.json --dry-run
```

JSON payload schema:

- `token_in` (address)
- `token_out` (address)
- `amount_in` (integer base units)
- `condition_type` (`TARGET_SQRT_PRICE_X96` or `MAX_SLIPPAGE_BPS`)
- `condition_value` (integer)
- `expiry` (unix timestamp in seconds)

### Create Intent from Text (Gemini)

```bash
uv run python -m agent.cli.main intent create --text "Swap 1000000 units of token0 to token1 when slippage <= 100 bps before 1735689600"
uv run python -m agent.cli.main intent create --text "..." --dry-run
```

## Agent Commands

### Continuous Loop

```bash
uv run python -m agent.cli.main agent run
uv run python -m agent.cli.main agent run --interval-ms 5000
```

### Single Pass

```bash
uv run python -m agent.cli.main agent run-once
uv run python -m agent.cli.main agent run-once --dry-run
uv run python -m agent.cli.main agent run-once --interval-ms 5000
```

## Structured Event Codes

`agent run` and `agent run-once` emit JSON event lines from `agent/execution_engine.py`.

Execution flow codes:

- `SKIP_EXECUTED`
- `SKIP_EXPIRED`
- `SKIP_NOT_EXECUTABLE`
- `SKIP_INFLIGHT`
- `DRY_RUN_EXECUTABLE`
- `EXECUTE_SUBMITTED`
- `EXECUTE_CONFIRMED`
- `EXECUTE_REVERTED`
- `EXECUTE_SUBMIT_FAILED`
- `PASS_SUMMARY`

Retry/inflight diagnostics:

- `RETRY_INTENT_COUNT`
- `RETRY_GET_INTENT`
- `RETRY_CAN_EXECUTE`
- `RETRY_SUBMIT_SWAP`
- `INFLIGHT_PENDING`
- `INFLIGHT_EXPIRED`
- `INFLIGHT_CHECK_FAILED`
