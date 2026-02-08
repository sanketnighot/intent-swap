import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable

from web3.exceptions import TransactionNotFound

from agent.state_store import StateStore
from agent.uniswap_client import (
    build_swap_params,
    can_execute_intent,
    create_runtime_clients,
    get_intent,
    get_intent_count,
    intent_id_to_hook_data,
    send_swap,
)


@dataclass
class EngineConfig:
    interval_ms: int
    retry_attempts: int
    retry_delay_ms: int
    inflight_ttl_sec: int
    state_file: str


def _to_int(name: str, default: int) -> int:
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


def load_engine_config(default_interval_ms: int, interval_override: int | None = None) -> EngineConfig:
    interval = default_interval_ms if interval_override is None else int(interval_override)
    if interval <= 0:
        raise RuntimeError("interval must be > 0")

    return EngineConfig(
        interval_ms=interval,
        retry_attempts=_to_int("EXECUTOR_RETRY_ATTEMPTS", 3),
        retry_delay_ms=_to_int("EXECUTOR_RETRY_DELAY_MS", 500),
        inflight_ttl_sec=_to_int("EXECUTOR_INFLIGHT_TTL_SEC", 600),
        state_file=os.getenv("EXECUTOR_STATE_FILE", ".intentswap-state.json").strip() or ".intentswap-state.json",
    )


def emit_event(code: str, **fields: Any) -> None:
    payload = {"ts": int(time.time()), "code": code, **fields}
    print(json.dumps(payload), file=sys.stdout)


def _with_retry(
    code: str,
    fn: Callable[[], Any],
    attempts: int,
    delay_ms: int,
    context: dict[str, Any] | None = None,
) -> Any:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as error:  # noqa: PERF203 - explicit retry loop
            last_error = error
            emit_event(
                code,
                attempt=attempt,
                attempts=attempts,
                error=str(error),
                **(context or {}),
            )
            if attempt < attempts:
                time.sleep(delay_ms / 1000.0)

    raise RuntimeError(f"retry exhausted for {code}: {last_error}")


def _reconcile_inflight(runtime: Any, store: StateStore, config: EngineConfig, summary: dict[str, int]) -> None:
    now = int(time.time())
    changed = False

    for intent_id in store.get_inflight_ids():
        inflight = store.get_inflight(intent_id)
        if inflight is None:
            continue

        try:
            receipt = runtime.w3.eth.get_transaction_receipt(inflight.tx_hash)
        except TransactionNotFound:
            age_sec = now - inflight.submitted_at
            if age_sec > config.inflight_ttl_sec:
                store.clear_inflight(intent_id)
                changed = True
                summary["inflight_expired"] += 1
                emit_event("INFLIGHT_EXPIRED", intent_id=intent_id, tx_hash=inflight.tx_hash, age_sec=age_sec)
            else:
                summary["inflight_pending"] += 1
                emit_event("INFLIGHT_PENDING", intent_id=intent_id, tx_hash=inflight.tx_hash, age_sec=age_sec)
            continue
        except Exception as error:
            summary["inflight_check_failed"] += 1
            emit_event(
                "INFLIGHT_CHECK_FAILED",
                intent_id=intent_id,
                tx_hash=inflight.tx_hash,
                error=str(error),
            )
            continue

        status = int(getattr(receipt, "status", 0))
        block_number = int(getattr(receipt, "blockNumber", 0))
        if status == 1:
            summary["confirmed"] += 1
            emit_event("EXECUTE_CONFIRMED", intent_id=intent_id, tx_hash=inflight.tx_hash, block_number=block_number)
        else:
            summary["reverted"] += 1
            emit_event("EXECUTE_REVERTED", intent_id=intent_id, tx_hash=inflight.tx_hash, block_number=block_number)

        store.clear_inflight(intent_id)
        changed = True

    if changed:
        store.save()


def _submit_execution(runtime: Any, intent_id: int, intent: Any) -> str:
    swap_params = build_swap_params(intent)
    hook_data = intent_id_to_hook_data(intent_id)
    return send_swap(runtime.w3, runtime.swap_target, runtime.pool_key, swap_params, hook_data, runtime.account)


def run_single_pass(
    interval_ms: int | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    runtime = create_runtime_clients()
    config = load_engine_config(runtime.poll_interval_ms, interval_override=interval_ms)
    store = StateStore(config.state_file)

    summary = {
        "seen": 0,
        "submitted": 0,
        "confirmed": 0,
        "reverted": 0,
        "skipped_executed": 0,
        "skipped_expired": 0,
        "skipped_not_executable": 0,
        "skipped_inflight": 0,
        "read_failures": 0,
        "submit_failures": 0,
        "inflight_pending": 0,
        "inflight_expired": 0,
        "inflight_check_failed": 0,
        "dry_run_executable": 0,
    }

    _reconcile_inflight(runtime, store, config, summary)

    total_intents = _with_retry(
        "RETRY_INTENT_COUNT",
        lambda: get_intent_count(runtime),
        attempts=config.retry_attempts,
        delay_ms=config.retry_delay_ms,
    )
    now = int(time.time())

    for intent_id in range(total_intents):
        summary["seen"] += 1

        if store.has_inflight(intent_id):
            summary["skipped_inflight"] += 1
            emit_event("SKIP_INFLIGHT", intent_id=intent_id)
            continue

        try:
            intent = _with_retry(
                "RETRY_GET_INTENT",
                lambda iid=intent_id: get_intent(runtime, iid),
                attempts=config.retry_attempts,
                delay_ms=config.retry_delay_ms,
                context={"intent_id": intent_id},
            )
        except Exception as error:
            summary["read_failures"] += 1
            emit_event("READ_FAILED", intent_id=intent_id, error=str(error))
            continue

        if bool(intent["executed"]):
            summary["skipped_executed"] += 1
            emit_event("SKIP_EXECUTED", intent_id=intent_id)
            continue

        if int(intent["expiry"]) <= now:
            summary["skipped_expired"] += 1
            emit_event("SKIP_EXPIRED", intent_id=intent_id, expiry=int(intent["expiry"]))
            continue

        try:
            executable = _with_retry(
                "RETRY_CAN_EXECUTE",
                lambda iid=intent_id, data=intent: can_execute_intent(runtime, iid, data),
                attempts=config.retry_attempts,
                delay_ms=config.retry_delay_ms,
                context={"intent_id": intent_id},
            )
        except Exception as error:
            summary["read_failures"] += 1
            emit_event("CHECK_FAILED", intent_id=intent_id, error=str(error))
            continue

        if not executable:
            summary["skipped_not_executable"] += 1
            emit_event("SKIP_NOT_EXECUTABLE", intent_id=intent_id)
            continue

        if dry_run:
            summary["dry_run_executable"] += 1
            emit_event("DRY_RUN_EXECUTABLE", intent_id=intent_id)
            continue

        try:
            tx_hash = _with_retry(
                "RETRY_SUBMIT_SWAP",
                lambda iid=intent_id, data=intent: _submit_execution(runtime, iid, data),
                attempts=config.retry_attempts,
                delay_ms=config.retry_delay_ms,
                context={"intent_id": intent_id},
            )
        except Exception as error:
            summary["submit_failures"] += 1
            emit_event("EXECUTE_SUBMIT_FAILED", intent_id=intent_id, error=str(error))
            continue

        summary["submitted"] += 1
        store.set_inflight(intent_id, tx_hash)
        store.save()
        emit_event("EXECUTE_SUBMITTED", intent_id=intent_id, tx_hash=tx_hash)

    emit_event("PASS_SUMMARY", **summary)
    return summary


def run_forever(interval_ms: int | None = None) -> None:
    runtime = create_runtime_clients()
    config = load_engine_config(runtime.poll_interval_ms, interval_override=interval_ms)

    while True:
        try:
            run_single_pass(interval_ms=config.interval_ms, dry_run=False)
        except Exception as error:
            emit_event("PASS_FAILED", error=str(error))
        time.sleep(config.interval_ms / 1000.0)

