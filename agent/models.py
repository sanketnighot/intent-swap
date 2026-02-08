from pydantic import BaseModel, ConfigDict, Field, field_validator

CONDITION_TARGET = "TARGET_SQRT_PRICE_X96"
CONDITION_SLIPPAGE = "MAX_SLIPPAGE_BPS"
ALLOWED_CONDITIONS = {CONDITION_TARGET, CONDITION_SLIPPAGE}


class ParsedIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token_in: str = Field(min_length=42, max_length=42)
    token_out: str = Field(min_length=42, max_length=42)
    amount_in: int = Field(gt=0, description="Input token amount in base units")
    condition_type: str
    condition_value: int = Field(ge=0)
    expiry: int = Field(gt=0, description="Unix timestamp in seconds")

    @field_validator("condition_type")
    @classmethod
    def normalize_condition_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in ALLOWED_CONDITIONS:
            allowed = ", ".join(sorted(ALLOWED_CONDITIONS))
            raise ValueError(f"condition_type must be one of: {allowed}")
        return normalized

