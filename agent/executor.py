#!/usr/bin/env python3

import os
import sys
import time
from typing import Any

from dotenv import load_dotenv
from web3 import Web3

HOOK_ABI: list[dict[str, Any]] = [
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


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def build_pool_key(hook_address: str) -> dict[str, Any]:
    return {
        "currency0": Web3.to_checksum_address(required_env("POOL_CURRENCY0")),
        "currency1": Web3.to_checksum_address(required_env("POOL_CURRENCY1")),
        "fee": int(required_env("POOL_FEE")),
        "tickSpacing": int(required_env("POOL_TICK_SPACING")),
        "hooks": Web3.to_checksum_address(hook_address),
    }


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


def poll_once(
    w3: Web3,
    hook: Any,
    swap_target: Any,
    pool_key: dict[str, Any],
    account: Any,
) -> None:
    total_intents = int(hook.functions.intentCount().call())
    now = int(time.time())

    for intent_id in range(total_intents):
        intent = hook.functions.getIntent(intent_id).call()

        if intent["executed"]:
            continue
        if int(intent["expiry"]) <= now:
            continue

        swap_params = build_swap_params(intent)

        try:
            executable = bool(hook.functions.canExecuteIntent(intent_id, pool_key, swap_params).call())
        except Exception as error:
            print(f"[intent {intent_id}] canExecuteIntent failed: {error}", file=sys.stderr)
            continue

        if not executable:
            continue

        hook_data = intent_id_to_hook_data(intent_id)
        try:
            tx_hash = send_swap(w3, swap_target, pool_key, swap_params, hook_data, account)
            print(f"[intent {intent_id}] submitted tx: {tx_hash}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"[intent {intent_id}] confirmed in block: {receipt.blockNumber}")
        except Exception as error:
            print(f"[intent {intent_id}] swap failed: {error}", file=sys.stderr)


def main() -> None:
    load_dotenv()

    rpc_url = required_env("RPC_URL")
    private_key = required_env("PRIVATE_KEY")
    hook_address = Web3.to_checksum_address(required_env("HOOK_ADDRESS"))
    swap_target_address = Web3.to_checksum_address(required_env("SWAP_TARGET_ADDRESS"))
    poll_interval_ms = int(os.getenv("POLL_INTERVAL_MS", "15000"))

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError("Could not connect to RPC_URL")

    account = w3.eth.account.from_key(private_key)
    hook = w3.eth.contract(address=hook_address, abi=HOOK_ABI)
    swap_target = w3.eth.contract(address=swap_target_address, abi=SWAP_TARGET_ABI)
    pool_key = build_pool_key(hook_address)

    while True:
        try:
            poll_once(w3, hook, swap_target, pool_key, account)
        except Exception as error:
            print(f"Polling error: {error}", file=sys.stderr)
        time.sleep(poll_interval_ms / 1000.0)


if __name__ == "__main__":
    main()
