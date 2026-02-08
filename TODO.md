# IntentSwap Development TODO

Last updated: 2026-02-08

## Status Legend

- `[ ]` Not started
- `[-]` In progress
- `[x]` Done
- `[!]` Blocked

## Phase 0: Project Baseline

- [x] Cross-agent rules and docs (`AGENTS.md`, `CLAUDE.md`, `CODEX.md`, Cursor/Copilot rules)
- [x] Judge-facing docs (`docs/judge-brief.md`, `docs/demo-script.md`)
- [x] Python runtime setup with `uv` (`pyproject.toml`)
- [x] Minimal execution agent in Python (`agent/executor.py`)
- [x] Initial hook contract (`contracts/IntentSwapHook.sol`)

## Phase 1: CLI Foundation

- [x] Create CLI entrypoint `agent/cli/main.py`
- [x] Add CLI command groups: `intent`, `agent`, `config`
- [x] Implement `config validate` command
- [x] Add unified output mode (`--json` for machine-readable output)
- [x] Add `--dry-run` support for tx-producing commands

Acceptance criteria:
- CLI starts with `uv run python -m agent.cli.main --help`
- Env validation errors are actionable

## Phase 2: Deterministic Intent Operations

- [x] Implement `intent list`
- [x] Implement `intent show --id`
- [x] Implement `intent can-execute --id`
- [x] Implement `intent execute --id`
- [x] Refactor onchain calls into `agent/uniswap_client.py`

Acceptance criteria:
- Commands read real onchain intents
- `intent execute` only sends tx after deterministic prechecks

## Phase 3: Gemini Intent Parsing (Bounded Role)

- [ ] Add Gemini client module `agent/gemini_client.py`
- [ ] Add strict typed models in `agent/models.py`
- [ ] Add deterministic validator in `agent/validator.py`
- [ ] Implement `intent create --text "..."`
- [ ] Implement `intent create --json <file>`
- [ ] Reject malformed/ambiguous LLM output (fail closed)

Acceptance criteria:
- LLM output is schema-constrained
- No tx is sent if parser/validation fails

## Phase 4: Autonomous Executor Hardening

- [ ] Refactor loop into `agent/execution_engine.py`
- [ ] Add idempotency + in-flight tracking in `agent/state_store.py`
- [ ] Add retry policy and timeout handling
- [ ] Add structured reason codes in logs
- [ ] Implement `agent run-once`
- [ ] Implement `agent run --interval-ms`

Acceptance criteria:
- No duplicate tx spam for same intent
- Restart behavior is safe and predictable

## Phase 5: Testing

- [ ] Add unit tests for validators and encoders
- [ ] Add unit tests for CLI command behavior
- [ ] Add integration tests for execution flow
- [ ] Add contract behavior tests for expiry/executed/mismatch/price checks
- [ ] Add test command docs in README

Acceptance criteria:
- Core happy path and failure paths are covered
- Test instructions are reproducible

## Phase 6: Submission-Ready Packaging

- [ ] Add `docs/cli-reference.md`
- [ ] Update README with full CLI command reference
- [ ] Add evidence capture checklist with tx IDs
- [ ] Verify demo script against real commands and outputs

Acceptance criteria:
- New contributor can run setup + demo without guesswork
- Submission materials match implemented behavior

## Current Sprint (Start Here)

- [x] Create and maintain this TODO tracker
- [x] Implement CLI entrypoint and `config validate`
- [x] Extract onchain client module and wire existing executor to it
- [ ] Start Gemini integration scaffolding (`models.py`, `validator.py`, `gemini_client.py`)

## Open Decisions

- [x] Choose CLI framework (`argparse`, standard library for zero extra dependency)
- [ ] Decide state store format (`sqlite` vs local json file)
- [ ] Confirm target test environment (`anvil`/`hardhat`/testnet)
