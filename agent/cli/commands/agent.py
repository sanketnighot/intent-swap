from argparse import Namespace

from agent import executor
from agent.cli.output import emit_result


def handle_agent_run(args: Namespace) -> int:
    if args.dry_run:
        emit_result(
            args.json_output,
            status="dry_run",
            message="agent run dry-run does not start the execution loop",
        )
        return 0

    emit_result(
        args.json_output,
        status="ok",
        message="Starting execution agent loop",
        details={"interval_ms": args.interval_ms},
    )
    executor.run_forever(interval_ms=args.interval_ms)
    return 0


def handle_agent_run_once(args: Namespace) -> int:
    if args.dry_run:
        emit_result(
            args.json_output,
            status="dry_run",
            message="agent run-once dry-run does not submit any transaction",
        )
        return 0

    emit_result(
        args.json_output,
        status="not_implemented",
        message="agent run-once is planned for Phase 4",
    )
    return 2
