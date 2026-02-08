---
name: intentswap-engineering
description: Use this skill when implementing or modifying IntentSwap core code (hook contract, execution agent, deploy flow) while preserving deterministic onchain enforcement and non-speculative behavior.
---

# IntentSwap Engineering Skill

Use this skill for code changes in:

- `contracts/IntentSwapHook.sol`
- `agent/executor.py`
- `scripts/deploy.js`
- `.env.example`
- `README.md` and architecture docs

## Workflow

1. Read `references/constraints.md`.
2. Read `references/workflow.md`.
3. Inspect only files needed for the requested change.
4. Implement minimal explicit logic.
5. Run relevant checks and report command outputs.
6. Update docs if interfaces or behavior changed.

## When To Use

Trigger this skill when requests include:

- intent condition logic changes
- hook callback validation changes
- agent execution behavior changes
- env/config/run command changes

## Avoid

- speculative strategy logic
- hidden abstractions that obscure validation
- offchain checks that replace onchain checks
