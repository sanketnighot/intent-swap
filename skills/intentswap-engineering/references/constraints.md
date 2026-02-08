# Constraints Reference

## Core Invariants

1. Hook enforcement is authoritative.
2. Offchain execution is untrusted coordination.
3. No custody of user funds.
4. No predictive AI claims or strategy optimization.

## Engineering Rules

- Prefer explicit logic over abstraction.
- Keep state and control flow minimal.
- Revert or fail closed on invalid conditions.
- Preserve readable line-by-line behavior.

## Required Alignment

- Reliability: onchain checks and deterministic logic.
- Transparency: clear intent fields and execution reasons.
- Composability: any executor can participate.
