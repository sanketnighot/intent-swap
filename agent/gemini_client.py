import json
import os
from urllib import error, parse, request

from agent.models import ParsedIntent

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value == "":
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _extract_json_object(text: str) -> dict[str, object]:
    stripped = text.strip()

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
            stripped = "\n".join(lines[1:-1]).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError("Gemini response does not contain a JSON object")

    return json.loads(stripped[start : end + 1])


def _build_prompt(text: str, pool_key: dict[str, object]) -> str:
    currency0 = str(pool_key["currency0"])
    currency1 = str(pool_key["currency1"])

    return (
        "Convert the user instruction into a strict JSON object with these fields only:\n"
        "token_in (address), token_out (address), amount_in (integer base units), "
        "condition_type (TARGET_SQRT_PRICE_X96 or MAX_SLIPPAGE_BPS), condition_value (integer), "
        "expiry (unix timestamp seconds).\n"
        "Rules:\n"
        f"- token_in and token_out must be one of pool currencies: {currency0} or {currency1}\n"
        "- amount_in must be integer base units (wei-like, no decimals)\n"
        "- condition_type must be uppercase enum value\n"
        "- if condition_type is MAX_SLIPPAGE_BPS then condition_value must be 0..10000\n"
        "- expiry must be a future unix timestamp in seconds\n"
        "Output JSON only, with no extra keys.\n\n"
        f"Instruction:\n{text}"
    )


def parse_intent_text_with_gemini(text: str, pool_key: dict[str, object]) -> ParsedIntent:
    api_key = _required_env("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip() or "gemini-2.0-flash"
    timeout_ms = int(os.getenv("GEMINI_TIMEOUT_MS", "15000"))

    prompt = _build_prompt(text, pool_key)
    url = f"{GEMINI_API_BASE}/{parse.quote(model)}:generateContent?key={parse.quote(api_key)}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
        },
    }

    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_ms / 1000.0) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Gemini request failed: {exc.reason}") from exc

    try:
        text_out = raw["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Gemini response shape: {raw}") from exc

    parsed_json = _extract_json_object(text_out)
    return ParsedIntent.model_validate(parsed_json)

