import json
import time
from dataclasses import dataclass

from web3 import Web3

from agent.models import CONDITION_SLIPPAGE, CONDITION_TARGET, ParsedIntent

CONDITION_TYPE_TO_ENUM = {
    CONDITION_TARGET: 0,
    CONDITION_SLIPPAGE: 1,
}


@dataclass
class ValidatedIntent:
    token_in: str
    token_out: str
    amount_in: int
    condition_type: str
    condition_type_enum: int
    condition_value: int
    expiry: int
    zero_for_one: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "token_in": self.token_in,
            "token_out": self.token_out,
            "amount_in": self.amount_in,
            "condition_type": self.condition_type,
            "condition_type_enum": self.condition_type_enum,
            "condition_value": self.condition_value,
            "expiry": self.expiry,
            "zero_for_one": self.zero_for_one,
        }


def load_parsed_intent_from_json_file(path: str) -> ParsedIntent:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return ParsedIntent.model_validate(payload)


def validate_parsed_intent(parsed: ParsedIntent, pool_key: dict[str, object]) -> ValidatedIntent:
    token_in = Web3.to_checksum_address(parsed.token_in)
    token_out = Web3.to_checksum_address(parsed.token_out)
    currency0 = Web3.to_checksum_address(str(pool_key["currency0"]))
    currency1 = Web3.to_checksum_address(str(pool_key["currency1"]))

    if token_in == token_out:
        raise RuntimeError("token_in and token_out must differ")

    if token_in == currency0 and token_out == currency1:
        zero_for_one = True
    elif token_in == currency1 and token_out == currency0:
        zero_for_one = False
    else:
        raise RuntimeError("token_in/token_out must match pool currency pair from environment")

    now = int(time.time())
    if parsed.expiry <= now:
        raise RuntimeError("expiry must be in the future")

    if parsed.condition_type == CONDITION_SLIPPAGE and parsed.condition_value > 10_000:
        raise RuntimeError("MAX_SLIPPAGE_BPS condition_value must be <= 10000")

    if parsed.condition_type == CONDITION_TARGET and parsed.condition_value == 0:
        raise RuntimeError("TARGET_SQRT_PRICE_X96 condition_value must be > 0")

    return ValidatedIntent(
        token_in=token_in,
        token_out=token_out,
        amount_in=int(parsed.amount_in),
        condition_type=parsed.condition_type,
        condition_type_enum=CONDITION_TYPE_TO_ENUM[parsed.condition_type],
        condition_value=int(parsed.condition_value),
        expiry=int(parsed.expiry),
        zero_for_one=zero_for_one,
    )

