# Agent Playbook

This playbook is for autonomous coding agents working in this repository.

## Quick Start

1. Read `AGENTS.md`.
2. Read `docs/architecture.md`.
3. Read `README.md` for run commands and environment variables.

## Standard Task Loop

1. Confirm scope and constraints.
2. Inspect affected files only.
3. Implement minimal explicit changes.
4. Run relevant checks.
5. Update docs if behavior changed.
6. Summarize changed files and validation.

## Validation Commands

Use only what is relevant to the change.

```bash
python3 -m py_compile agent/executor.py
node --check scripts/deploy.js
```

If a Solidity toolchain is available, run compile/tests for contract changes.

## Change Safety

- Never rely on offchain logic to enforce correctness.
- Never claim validations that were not executed.
- Prefer incremental edits over large rewrites.

## Communication Style

- Be direct and technical.
- Call out assumptions clearly.
- Include concrete next steps only when useful.
