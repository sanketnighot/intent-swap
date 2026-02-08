# IntentSwap Judge Brief

IntentSwap introduces an agent-driven execution layer for Uniswap v4 where users submit conditional swap intents instead of executing swaps immediately. Offchain executors monitor onchain state and submit execution transactions only when intent constraints are satisfied, while a Uniswap v4 hook enforces all conditions in `beforeSwap` at protocol level. This design separates decision timing from execution enforcement, improves reliability via deterministic onchain validation, preserves transparency through explicit intent state, and stays non-speculative by using rule-based execution rather than predictive intelligence.

## Key Talking Points

- Agentic, not speculative: continuous autonomous execution coordination, no price prediction.
- Hook-enforced correctness: invalid execution attempts revert onchain.
- Composable architecture: any actor can run an executor; trust is placed in contract logic.
- Clear user benefit: conditional execution instead of immediate, timing-sensitive swaps.
