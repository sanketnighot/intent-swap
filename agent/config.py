import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv
from web3 import Web3

AGENT_PROFILE = "agent"
DEPLOY_PROFILE = "deploy"

AGENT_REQUIRED_ENV = [
    "RPC_URL",
    "PRIVATE_KEY",
    "HOOK_ADDRESS",
    "SWAP_TARGET_ADDRESS",
    "POOL_CURRENCY0",
    "POOL_CURRENCY1",
    "POOL_FEE",
    "POOL_TICK_SPACING",
]

DEPLOY_REQUIRED_ENV = [
    "RPC_URL",
    "PRIVATE_KEY",
    "POOL_MANAGER_ADDRESS",
]

ADDRESS_ENV_KEYS = [
    "HOOK_ADDRESS",
    "SWAP_TARGET_ADDRESS",
    "POOL_CURRENCY0",
    "POOL_CURRENCY1",
    "POOL_MANAGER_ADDRESS",
]

PRIVATE_KEY_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
RPC_URL_PREFIXES = ("http://", "https://", "ws://", "wss://")


@dataclass
class ValidationReport:
    profile: str
    missing: list[str]
    invalid: dict[str, str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return len(self.missing) == 0 and len(self.invalid) == 0

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "profile": self.profile,
            "missing": self.missing,
            "invalid": self.invalid,
            "warnings": self.warnings,
        }


def _validate_rpc_url(value: str) -> str | None:
    if not value.startswith(RPC_URL_PREFIXES):
        return "RPC_URL must start with http://, https://, ws://, or wss://"
    return None


def _validate_private_key(value: str) -> str | None:
    if not PRIVATE_KEY_RE.match(value):
        return "PRIVATE_KEY must be a 32-byte hex string (0x + 64 hex chars)"
    return None


def _validate_address(value: str) -> str | None:
    if not Web3.is_address(value):
        return "must be a valid EVM address"
    return None


def _validate_positive_int(name: str, value: str) -> str | None:
    try:
        parsed = int(value)
    except ValueError:
        return f"{name} must be an integer"
    if parsed <= 0:
        return f"{name} must be > 0"
    return None


def _validate_int24(name: str, value: str) -> str | None:
    try:
        parsed = int(value)
    except ValueError:
        return f"{name} must be an integer"
    if parsed < -(2**23) or parsed > (2**23 - 1):
        return f"{name} must fit in int24 range"
    if parsed == 0:
        return f"{name} must be non-zero"
    return None


def validate_environment(profile: str = AGENT_PROFILE) -> ValidationReport:
    load_dotenv()

    if profile == AGENT_PROFILE:
        required = AGENT_REQUIRED_ENV
    elif profile == DEPLOY_PROFILE:
        required = DEPLOY_REQUIRED_ENV
    else:
        return ValidationReport(
            profile=profile,
            missing=[],
            invalid={"profile": f"unsupported profile '{profile}'"},
            warnings=[],
        )

    missing: list[str] = []
    invalid: dict[str, str] = {}
    warnings: list[str] = []

    for key in required:
        value = os.getenv(key, "").strip()
        if value == "":
            missing.append(key)

    if "RPC_URL" not in missing:
        issue = _validate_rpc_url(os.environ["RPC_URL"].strip())
        if issue:
            invalid["RPC_URL"] = issue

    if "PRIVATE_KEY" not in missing:
        issue = _validate_private_key(os.environ["PRIVATE_KEY"].strip())
        if issue:
            invalid["PRIVATE_KEY"] = issue

    for key in ADDRESS_ENV_KEYS:
        if key in required and key not in missing:
            issue = _validate_address(os.environ[key].strip())
            if issue:
                invalid[key] = issue

    if profile == AGENT_PROFILE:
        if "POOL_FEE" not in missing:
            issue = _validate_positive_int("POOL_FEE", os.environ["POOL_FEE"].strip())
            if issue:
                invalid["POOL_FEE"] = issue

        if "POOL_TICK_SPACING" not in missing:
            issue = _validate_int24("POOL_TICK_SPACING", os.environ["POOL_TICK_SPACING"].strip())
            if issue:
                invalid["POOL_TICK_SPACING"] = issue

        poll_interval = os.getenv("POLL_INTERVAL_MS", "").strip()
        if poll_interval != "":
            issue = _validate_positive_int("POLL_INTERVAL_MS", poll_interval)
            if issue:
                invalid["POLL_INTERVAL_MS"] = issue
        else:
            warnings.append("POLL_INTERVAL_MS not set, defaulting to 15000")

    return ValidationReport(profile=profile, missing=missing, invalid=invalid, warnings=warnings)

