import pathlib
import unittest

REPO_ROOT = pathlib.Path("/Users/sanket/MyProjects/Hackathon/intent-swap")
CONTRACT_PATH = REPO_ROOT / "contracts" / "IntentSwapHook.sol"


class ContractGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = CONTRACT_PATH.read_text(encoding="utf-8")

    def assertContains(self, snippet: str) -> None:  # type: ignore[override]
        self.assertIn(snippet, self.source, msg=f"Missing expected guard snippet: {snippet}")

    def test_expiry_guard(self) -> None:
        self.assertContains("if (block.timestamp > intent.expiry) revert IntentExpired();")

    def test_already_executed_guard(self) -> None:
        self.assertContains("if (intent.executed) revert IntentAlreadyExecuted();")

    def test_pool_mismatch_guard(self) -> None:
        self.assertContains("if (PoolId.unwrap(key.toId()) != PoolId.unwrap(intent.poolId)) revert PoolMismatch();")

    def test_direction_mismatch_guard(self) -> None:
        self.assertContains("if (params.zeroForOne != intent.zeroForOne) revert DirectionMismatch();")

    def test_amount_mismatch_guard(self) -> None:
        self.assertContains(
            "if (params.amountSpecified <= 0 || uint256(params.amountSpecified) != intent.amountIn) revert AmountMismatch();"
        )

    def test_token_mismatch_guard(self) -> None:
        self.assertContains("if (swapTokenIn != intent.tokenIn || swapTokenOut != intent.tokenOut) revert TokenMismatch();")

    def test_price_condition_guard(self) -> None:
        self.assertContains("if (!_meetsPriceCondition(intent, currentSqrtPriceX96)) revert PriceConditionNotMet();")


if __name__ == "__main__":
    unittest.main()

