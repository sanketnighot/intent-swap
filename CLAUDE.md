# Claude Code Instructions

Follow `AGENTS.md` as the primary project contract.

## Session Start Checklist

1. Read `AGENTS.md`.
2. Read `README.md`.
3. Read `docs/architecture.md` for system boundaries.
4. Confirm scope before implementing.

## Implementation Rules

- Keep onchain enforcement in `contracts/IntentSwapHook.sol` as the authority.
- Keep offchain execution deterministic and idempotent.
- Avoid broad refactors unless explicitly requested.
- Do not add speculative strategy logic.

## Response Expectations

- List changed files explicitly.
- State assumptions and unresolved risks.
- Include exact commands used for validation.

## Preferred Command Style

- Use `rg` / `rg --files` for search.
- Use targeted file edits; avoid unrelated churn.
- Avoid destructive git commands unless explicitly requested.
