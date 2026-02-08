import json


def _json_default(value: object) -> str:
    if isinstance(value, (bytes, bytearray)):
        return f"0x{value.hex()}"
    return str(value)


def emit_result(
    json_output: bool,
    status: str,
    message: str,
    details: dict[str, object] | None = None,
) -> None:
    payload = {"status": status, "message": message}
    if details:
        payload["details"] = details

    if json_output:
        print(json.dumps(payload, default=_json_default))
        return

    print(f"[{status}] {message}")
    if details:
        for key, value in details.items():
            print(f"- {key}: {value}")
