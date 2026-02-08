#!/usr/bin/env python3

import sys
import time

from agent.uniswap_client import (
    RuntimeClients,
    build_swap_params,
    create_runtime_clients,
    intent_id_to_hook_data,
    send_swap,
)


def poll_once(runtime: RuntimeClients) -> None:
    total_intents = int(runtime.hook.functions.intentCount().call())
    now = int(time.time())

    for intent_id in range(total_intents):
        intent = runtime.hook.functions.getIntent(intent_id).call()

        if intent["executed"]:
            continue
        if int(intent["expiry"]) <= now:
            continue

        swap_params = build_swap_params(intent)

        try:
            executable = bool(
                runtime.hook.functions.canExecuteIntent(intent_id, runtime.pool_key, swap_params).call()
            )
        except Exception as error:
            print(f"[intent {intent_id}] canExecuteIntent failed: {error}", file=sys.stderr)
            continue

        if not executable:
            continue

        hook_data = intent_id_to_hook_data(intent_id)
        try:
            tx_hash = send_swap(
                runtime.w3,
                runtime.swap_target,
                runtime.pool_key,
                swap_params,
                hook_data,
                runtime.account,
            )
            print(f"[intent {intent_id}] submitted tx: {tx_hash}")
            receipt = runtime.w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"[intent {intent_id}] confirmed in block: {receipt.blockNumber}")
        except Exception as error:
            print(f"[intent {intent_id}] swap failed: {error}", file=sys.stderr)


def run_forever(interval_ms: int | None = None) -> None:
    runtime = create_runtime_clients()
    effective_interval_ms = runtime.poll_interval_ms if interval_ms is None else interval_ms

    while True:
        try:
            poll_once(runtime)
        except Exception as error:
            print(f"Polling error: {error}", file=sys.stderr)
        time.sleep(effective_interval_ms / 1000.0)


def main() -> None:
    run_forever()


if __name__ == "__main__":
    main()

