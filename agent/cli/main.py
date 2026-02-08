import argparse
import sys

from dotenv import load_dotenv

from agent.cli.commands.agent import handle_agent_run, handle_agent_run_once
from agent.cli.commands.config import handle_config_validate
from agent.cli.commands.intent import (
    handle_intent_can_execute,
    handle_intent_create,
    handle_intent_execute,
    handle_intent_list,
    handle_intent_show,
)
from agent.cli.output import emit_result
from agent.config import AGENT_PROFILE, DEPLOY_PROFILE, GEMINI_PROFILE


def _common_flags_parent() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        default=argparse.SUPPRESS,
        help="Emit machine-readable JSON output",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Do not send transactions for tx-producing commands",
    )
    return parser


def build_parser() -> argparse.ArgumentParser:
    common = _common_flags_parent()

    parser = argparse.ArgumentParser(
        prog="intentswap",
        description="IntentSwap CLI",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit machine-readable JSON output",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not send transactions for tx-producing commands",
    )
    root_subparsers = parser.add_subparsers(dest="group")

    intent_parser = root_subparsers.add_parser("intent", help="Intent commands")
    intent_subparsers = intent_parser.add_subparsers(dest="intent_command")

    intent_list_parser = intent_subparsers.add_parser(
        "list",
        help="List intents",
        parents=[common],
    )
    intent_list_parser.set_defaults(handler=handle_intent_list)

    intent_show_parser = intent_subparsers.add_parser(
        "show",
        help="Show a specific intent",
        parents=[common],
    )
    intent_show_parser.add_argument("--id", required=True, type=int, dest="intent_id")
    intent_show_parser.set_defaults(handler=handle_intent_show)

    intent_can_execute_parser = intent_subparsers.add_parser(
        "can-execute",
        help="Check if an intent is currently executable",
        parents=[common],
    )
    intent_can_execute_parser.add_argument("--id", required=True, type=int, dest="intent_id")
    intent_can_execute_parser.set_defaults(handler=handle_intent_can_execute)

    intent_execute_parser = intent_subparsers.add_parser(
        "execute",
        help="Execute a single intent",
        parents=[common],
    )
    intent_execute_parser.add_argument("--id", required=True, type=int, dest="intent_id")
    intent_execute_parser.set_defaults(handler=handle_intent_execute)

    intent_create_parser = intent_subparsers.add_parser(
        "create",
        help="Create a new intent",
        parents=[common],
    )
    input_group = intent_create_parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", type=str, help="Natural-language intent description")
    input_group.add_argument("--json-file", type=str, help="Path to JSON intent payload")
    intent_create_parser.set_defaults(handler=handle_intent_create)

    agent_parser = root_subparsers.add_parser("agent", help="Agent process commands")
    agent_subparsers = agent_parser.add_subparsers(dest="agent_command")

    agent_run_parser = agent_subparsers.add_parser(
        "run",
        help="Run continuous executor loop",
        parents=[common],
    )
    agent_run_parser.add_argument(
        "--interval-ms",
        type=int,
        default=None,
        help="Polling interval override in milliseconds",
    )
    agent_run_parser.set_defaults(handler=handle_agent_run)

    agent_run_once_parser = agent_subparsers.add_parser(
        "run-once",
        help="Run a single poll/execute pass",
        parents=[common],
    )
    agent_run_once_parser.set_defaults(handler=handle_agent_run_once)

    config_parser = root_subparsers.add_parser("config", help="Configuration commands")
    config_subparsers = config_parser.add_subparsers(dest="config_command")

    config_validate_parser = config_subparsers.add_parser(
        "validate",
        help="Validate environment configuration",
        parents=[common],
    )
    config_validate_parser.add_argument(
        "--profile",
        choices=[AGENT_PROFILE, DEPLOY_PROFILE, GEMINI_PROFILE],
        default=AGENT_PROFILE,
        help="Validation profile",
    )
    config_validate_parser.set_defaults(handler=handle_config_validate)

    return parser


def main() -> int:
    load_dotenv()

    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, "json_output"):
        args.json_output = False
    if not hasattr(args, "dry_run"):
        args.dry_run = False

    if not hasattr(args, "handler"):
        parser.print_help()
        return 1

    try:
        return int(args.handler(args))
    except KeyboardInterrupt:
        emit_result(
            getattr(args, "json_output", False),
            status="error",
            message="Interrupted",
        )
        return 130
    except Exception as error:
        emit_result(
            getattr(args, "json_output", False),
            status="error",
            message=str(error),
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
