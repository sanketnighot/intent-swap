from argparse import Namespace

from agent.cli.output import emit_result
from agent.config import validate_environment


def handle_config_validate(args: Namespace) -> int:
    report = validate_environment(profile=args.profile)

    if report.ok:
        emit_result(
            args.json_output,
            status="ok",
            message=f"Configuration is valid for profile '{args.profile}'",
            details=report.to_dict(),
        )
        return 0

    emit_result(
        args.json_output,
        status="error",
        message=f"Configuration is invalid for profile '{args.profile}'",
        details=report.to_dict(),
    )
    return 1

