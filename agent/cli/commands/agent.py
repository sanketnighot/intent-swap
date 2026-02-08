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
    summary = executor.run_single_pass(interval_ms=args.interval_ms, dry_run=args.dry_run)

    emit_result(
        args.json_output,
        status="ok" if not args.dry_run else "dry_run",
        message="Completed one executor pass",
        details=summary,
    )
    return 0
