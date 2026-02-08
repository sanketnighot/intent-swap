import time
from argparse import Namespace

from agent.gemini_client import parse_intent_text_with_gemini
from agent.cli.output import emit_result
from agent.models import ParsedIntent
from agent.uniswap_client import (
    can_execute_intent,
    create_runtime_clients,
    execute_intent,
    get_intent,
    get_intent_count,
    intent_to_dict,
    load_pool_key_from_env,
    submit_intent,
)
from agent.validator import load_parsed_intent_from_json_file, validate_parsed_intent


def handle_intent_list(args: Namespace) -> int:
    runtime = create_runtime_clients()
    total = get_intent_count(runtime)
    now = int(time.time())
    intents: list[dict[str, object]] = []

    for intent_id in range(total):
        intent = get_intent(runtime, intent_id)
        item = intent_to_dict(intent_id, intent)
        if item["executed"]:
            item["state"] = "executed"
        elif int(item["expiry"]) <= now:
            item["state"] = "expired"
        else:
            item["state"] = "pending"
        intents.append(item)

    emit_result(
        args.json_output,
        status="ok",
        message=f"Fetched {len(intents)} intents",
        details={"count": len(intents), "intents": intents},
    )
    return 0


def handle_intent_show(args: Namespace) -> int:
    runtime = create_runtime_clients()
    intent = get_intent(runtime, args.intent_id)
    payload = intent_to_dict(args.intent_id, intent)

    emit_result(
        args.json_output,
        status="ok",
        message=f"Fetched intent {args.intent_id}",
        details=payload,
    )
    return 0


def handle_intent_can_execute(args: Namespace) -> int:
    runtime = create_runtime_clients()
    intent = get_intent(runtime, args.intent_id)
    executable = can_execute_intent(runtime, args.intent_id, intent)

    emit_result(
        args.json_output,
        status="ok",
        message=f"Intent {args.intent_id} executable={executable}",
        details={"intent_id": args.intent_id, "executable": executable},
    )
    return 0


def handle_intent_execute(args: Namespace) -> int:
    if args.dry_run:
        details: dict[str, object] = {"intent_id": args.intent_id}
        try:
            runtime = create_runtime_clients()
            intent = get_intent(runtime, args.intent_id)
            details["executable"] = can_execute_intent(runtime, args.intent_id, intent)
        except Exception as error:
            details["executable"] = None
            details["warning"] = str(error)
        emit_result(
            args.json_output,
            status="dry_run",
            message="No transaction sent for intent execute dry-run",
            details=details,
        )
        return 0

    runtime = create_runtime_clients()
    result = execute_intent(runtime, args.intent_id)
    if result["status"] == "executed":
        emit_result(
            args.json_output,
            status="ok",
            message=f"Intent {args.intent_id} executed",
            details=result,
        )
        return 0

    emit_result(
        args.json_output,
        status="skip",
        message=f"Intent {args.intent_id} not executed",
        details=result,
    )
    return 0


def handle_intent_create(args: Namespace) -> int:
    pool_key_context = load_pool_key_from_env()

    parsed_intent: ParsedIntent
    if args.text is not None:
        parsed_intent = parse_intent_text_with_gemini(args.text, pool_key_context)
    else:
        parsed_intent = load_parsed_intent_from_json_file(args.json_file)

    details: dict[str, object] = {"parsed_intent": parsed_intent.model_dump()}

    if args.dry_run:
        validated = validate_parsed_intent(parsed_intent, pool_key_context)
        details["validated_intent"] = validated.to_dict()

        emit_result(
            args.json_output,
            status="dry_run",
            message="No transaction sent for intent create dry-run",
            details=details,
        )
        return 0

    runtime = create_runtime_clients()
    validated_intent = validate_parsed_intent(parsed_intent, runtime.pool_key)
    submission = submit_intent(runtime, validated_intent.to_dict())

    details["validated_intent"] = validated_intent.to_dict()
    details["submission"] = submission
    emit_result(
        args.json_output,
        status="ok",
        message="Intent submitted",
        details=details,
    )
    return 0
