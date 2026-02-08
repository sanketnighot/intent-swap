import unittest

from agent.models import ParsedIntent
from agent.validator import validate_parsed_intent


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pool_key = {
            "currency0": "0x0000000000000000000000000000000000000001",
            "currency1": "0x0000000000000000000000000000000000000002",
            "fee": 3000,
            "tickSpacing": 60,
            "hooks": "0x0000000000000000000000000000000000000003",
        }

    def test_validate_success(self) -> None:
        parsed = ParsedIntent.model_validate(
            {
                "token_in": "0x0000000000000000000000000000000000000001",
                "token_out": "0x0000000000000000000000000000000000000002",
                "amount_in": 1000,
                "condition_type": "MAX_SLIPPAGE_BPS",
                "condition_value": 100,
                "expiry": 1893456000,
            }
        )
        validated = validate_parsed_intent(parsed, self.pool_key)
        self.assertTrue(validated.zero_for_one)
        self.assertEqual(validated.condition_type_enum, 1)

    def test_validate_rejects_invalid_pair(self) -> None:
        parsed = ParsedIntent.model_validate(
            {
                "token_in": "0x0000000000000000000000000000000000000010",
                "token_out": "0x0000000000000000000000000000000000000002",
                "amount_in": 1000,
                "condition_type": "MAX_SLIPPAGE_BPS",
                "condition_value": 100,
                "expiry": 1893456000,
            }
        )
        with self.assertRaisesRegex(RuntimeError, "must match pool currency pair"):
            validate_parsed_intent(parsed, self.pool_key)

    def test_validate_rejects_high_slippage(self) -> None:
        parsed = ParsedIntent.model_validate(
            {
                "token_in": "0x0000000000000000000000000000000000000001",
                "token_out": "0x0000000000000000000000000000000000000002",
                "amount_in": 1000,
                "condition_type": "MAX_SLIPPAGE_BPS",
                "condition_value": 10001,
                "expiry": 1893456000,
            }
        )
        with self.assertRaisesRegex(RuntimeError, "must be <= 10000"):
            validate_parsed_intent(parsed, self.pool_key)


if __name__ == "__main__":
    unittest.main()

