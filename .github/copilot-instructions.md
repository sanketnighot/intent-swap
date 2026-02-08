# Copilot Instructions For IntentSwap

Follow `AGENTS.md` for project-wide engineering constraints.

## Project Intent

- Build deterministic intent execution on Uniswap v4.
- Keep onchain hook enforcement as the final gate.
- Keep offchain agents transparent and rule-based.

## Coding Priorities

1. Correctness over optimization.
2. Explicit logic over abstraction.
3. Minimal state and clear validation paths.

## Guardrails

- Do not introduce speculative trading logic.
- Do not add frontend features unless requested.
- Do not bypass hook checks with offchain assumptions.

## Output Expectations

- Generate readable code with concise comments.
- Update docs when public behavior changes.
- Include assumptions for external dependencies.
