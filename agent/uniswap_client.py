import os
import time
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from web3 import Web3

HOOK_ABI: list[dict[str, Any]] = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "currency0", "type": "address"},
                    {"internalType": "address", "name": "currency1", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "int24", "name": "tickSpacing", "type": "int24"},
                    {"internalType": "address", "name": "hooks", "type": "address"},
                ],
                "internalType": "struct PoolKey",
                "name": "key",
                "type": "tuple",
            },
            {"internalType": "bool", "name": "zeroForOne", "type": "bool"},
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint8", "name": "conditionType", "type": "uint8"},
            {"internalType": "uint160", "name": "conditionValue", "type": "uint160"},
            {"internalType": "uint64", "name": "expiry", "type": "uint64"},
        ],
        "name": "submitIntent",
        "outputs": [{"internalType": "uint256", "name": "intentId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "intentCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "intentId", "type": "uint256"}],
        "name": "getIntent",
        "outputs": [
            {
                "components": [
                    {"internalType": "address", "name": "user", "type": "address"},
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint8", "name": "conditionType", "type": "uint8"},
                    {"internalType": "uint160", "name": "conditionValue", "type": "uint160"},
                    {"internalType": "uint64", "name": "expiry", "type": "uint64"},
                    {"internalType": "bool", "name": "executed", "type": "bool"},
                    {"internalType": "bytes32", "name": "poolId", "type": "bytes32"},
                    {"internalType": "bool", "name": "zeroForOne", "type": "bool"},
                    {
                        "internalType": "uint160",
                        "name": "referenceSqrtPriceX96",
                        "type": "uint160",
                    },
                ],
                "internalType": "struct IntentSwapHook.Intent",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "intentId", "type": "uint256"},
            {
                "components": [
                    {"internalType": "address", "name": "currency0", "type": "address"},
                    {"internalType": "address", "name": "currency1", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "int24", "name": "tickSpacing", "type": "int24"},
                    {"internalType": "address", "name": "hooks", "type": "address"},
                ],
                "internalType": "struct PoolKey",
                "name": "key",
                "type": "tuple",
            },
            {
                "components": [
                    {"internalType": "bool", "name": "zeroForOne", "type": "bool"},
                    {"internalType": "int256", "name": "amountSpecified", "type": "int256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "internalType": "struct IPoolManager.SwapParams",
                "name": "params",
                "type": "tuple",
            },
        ],
        "name": "canExecuteIntent",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]

SWAP_TARGET_ABI: list[dict[str, Any]] = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "currency0", "type": "address"},
                    {"internalType": "address", "name": "currency1", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "int24", "name": "tickSpacing", "type": "int24"},
                    {"internalType": "address", "name": "hooks", "type": "address"},
                ],
                "internalType": "struct PoolKey",
                "name": "key",
                "type": "tuple",
            },
            {
                "components": [
                    {"internalType": "bool", "name": "zeroForOne", "type": "bool"},
                    {"internalType": "int256", "name": "amountSpecified", "type": "int256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "internalType": "struct IPoolManager.SwapParams",
                "name": "params",
                "type": "tuple",
            },
            {"internalType": "bytes", "name": "hookData", "type": "bytes"},
        ],
        "name": "swap",
        "outputs": [
            {"internalType": "int256", "name": "amount0", "type": "int256"},
            {"internalType": "int256", "name": "amount1", "type": "int256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

MIN_SQRT_PRICE_LIMIT_X96 = 4_295_128_740
MAX_SQRT_PRICE_LIMIT_X96 = 1_461_446_703_485_210_103_287_273_052_203_988_822_378_723_970_341


@dataclass
class RuntimeClients:
    w3: Web3
    account: Any
    hook: Any
    swap_target: Any
    pool_key: dict[str, Any]
    poll_interval_ms: int
    rpc_timeout_sec: int
    receipt_timeout_sec: int


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _env_positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if raw == "":
        return default
    try:
        parsed = int(raw)
    except ValueError as error:
        raise RuntimeError(f"{name} must be an integer") from error
    if parsed <= 0:
        raise RuntimeError(f"{name} must be > 0")
    return parsed


def build_pool_key(hook_address: str) -> dict[str, Any]:
    return {
        "currency0": Web3.to_checksum_address(required_env("POOL_CURRENCY0")),
        "currency1": Web3.to_checksum_address(required_env("POOL_CURRENCY1")),
        "fee": int(required_env("POOL_FEE")),
        "tickSpacing": int(required_env("POOL_TICK_SPACING")),
        "hooks": Web3.to_checksum_address(hook_address),
    }


def load_pool_key_from_env() -> dict[str, Any]:
    hook_address = Web3.to_checksum_address(required_env("HOOK_ADDRESS"))
    return build_pool_key(hook_address)


def build_swap_params(intent: Any) -> dict[str, Any]:
    zero_for_one = bool(intent["zeroForOne"])
    return {
        "zeroForOne": zero_for_one,
        "amountSpecified": int(intent["amountIn"]),
        "sqrtPriceLimitX96": MIN_SQRT_PRICE_LIMIT_X96 if zero_for_one else MAX_SQRT_PRICE_LIMIT_X96,
    }


def intent_id_to_hook_data(intent_id: int) -> bytes:
    return intent_id.to_bytes(32, byteorder="big")


def send_swap(
    w3: Web3,
    swap_target: Any,
    pool_key: dict[str, Any],
    swap_params: dict[str, Any],
    hook_data: bytes,
    account: Any,
) -> str:
    tx = swap_target.functions.swap(pool_key, swap_params, hook_data).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": w3.eth.chain_id,
            "gasPrice": w3.eth.gas_price,
        }
    )

    if "gas" not in tx:
        tx["gas"] = w3.eth.estimate_gas(tx)

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()


def create_runtime_clients() -> RuntimeClients:
    load_dotenv()

    rpc_url = required_env("RPC_URL")
    private_key = required_env("PRIVATE_KEY")
    hook_address = Web3.to_checksum_address(required_env("HOOK_ADDRESS"))
    swap_target_address = Web3.to_checksum_address(required_env("SWAP_TARGET_ADDRESS"))
    poll_interval_ms = _env_positive_int("POLL_INTERVAL_MS", 15000)
    rpc_timeout_sec = _env_positive_int("RPC_TIMEOUT_SEC", 10)
    receipt_timeout_sec = _env_positive_int("RECEIPT_TIMEOUT_SEC", 120)

    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": rpc_timeout_sec}))
    if not w3.is_connected():
        raise RuntimeError("Could not connect to RPC_URL")

    account = w3.eth.account.from_key(private_key)
    hook = w3.eth.contract(address=hook_address, abi=HOOK_ABI)
    swap_target = w3.eth.contract(address=swap_target_address, abi=SWAP_TARGET_ABI)
    pool_key = build_pool_key(hook_address)

    return RuntimeClients(
        w3=w3,
        account=account,
        hook=hook,
        swap_target=swap_target,
        pool_key=pool_key,
        poll_interval_ms=poll_interval_ms,
        rpc_timeout_sec=rpc_timeout_sec,
        receipt_timeout_sec=receipt_timeout_sec,
    )


def _pool_id_to_hex(pool_id: Any) -> str:
    if isinstance(pool_id, (bytes, bytearray)):
        return f"0x{pool_id.hex()}"
    return str(pool_id)


def intent_to_dict(intent_id: int, intent: Any) -> dict[str, Any]:
    return {
        "intent_id": intent_id,
        "user": str(intent["user"]),
        "tokenIn": str(intent["tokenIn"]),
        "tokenOut": str(intent["tokenOut"]),
        "amountIn": int(intent["amountIn"]),
        "conditionType": int(intent["conditionType"]),
        "conditionValue": int(intent["conditionValue"]),
        "expiry": int(intent["expiry"]),
        "executed": bool(intent["executed"]),
        "poolId": _pool_id_to_hex(intent["poolId"]),
        "zeroForOne": bool(intent["zeroForOne"]),
        "referenceSqrtPriceX96": int(intent["referenceSqrtPriceX96"]),
    }


def get_intent_count(runtime: RuntimeClients) -> int:
    return int(runtime.hook.functions.intentCount().call())


def get_intent(runtime: RuntimeClients, intent_id: int) -> Any:
    return runtime.hook.functions.getIntent(intent_id).call()


def can_execute_intent(runtime: RuntimeClients, intent_id: int, intent: Any) -> bool:
    swap_params = build_swap_params(intent)
    return bool(runtime.hook.functions.canExecuteIntent(intent_id, runtime.pool_key, swap_params).call())


def execute_intent(runtime: RuntimeClients, intent_id: int) -> dict[str, Any]:
    intent = get_intent(runtime, intent_id)

    if bool(intent["executed"]):
        return {"status": "skip", "reason": "already_executed"}

    if int(intent["expiry"]) <= int(time.time()):
        return {"status": "skip", "reason": "expired"}

    executable = can_execute_intent(runtime, intent_id, intent)
    if not executable:
        return {"status": "skip", "reason": "not_executable"}

    swap_params = build_swap_params(intent)
    hook_data = intent_id_to_hook_data(intent_id)
    tx_hash = send_swap(runtime.w3, runtime.swap_target, runtime.pool_key, swap_params, hook_data, runtime.account)
    receipt = runtime.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=runtime.receipt_timeout_sec)

    return {
        "status": "executed",
        "tx_hash": tx_hash,
        "block_number": int(receipt.blockNumber),
    }


def submit_intent(runtime: RuntimeClients, validated_intent: dict[str, Any]) -> dict[str, Any]:
    tx = runtime.hook.functions.submitIntent(
        runtime.pool_key,
        bool(validated_intent["zero_for_one"]),
        int(validated_intent["amount_in"]),
        int(validated_intent["condition_type_enum"]),
        int(validated_intent["condition_value"]),
        int(validated_intent["expiry"]),
    ).build_transaction(
        {
            "from": runtime.account.address,
            "nonce": runtime.w3.eth.get_transaction_count(runtime.account.address),
            "chainId": runtime.w3.eth.chain_id,
            "gasPrice": runtime.w3.eth.gas_price,
        }
    )

    if "gas" not in tx:
        tx["gas"] = runtime.w3.eth.estimate_gas(tx)

    signed = runtime.account.sign_transaction(tx)
    tx_hash = runtime.w3.eth.send_raw_transaction(signed.raw_transaction).hex()
    receipt = runtime.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=runtime.receipt_timeout_sec)

    intent_id: int | None = None
    if receipt.logs:
        try:
            decoded = runtime.hook.events.IntentCreated().process_receipt(receipt)
            if decoded:
                intent_id = int(decoded[0]["args"]["intentId"])
        except Exception:
            intent_id = None

    return {
        "status": "submitted",
        "tx_hash": tx_hash,
        "block_number": int(receipt.blockNumber),
        "intent_id": intent_id,
    }
