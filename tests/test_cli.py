import json
import os
import subprocess
import tempfile
import unittest

REPO_ROOT = "/Users/sanket/MyProjects/Hackathon/intent-swap"


class CLITests(unittest.TestCase):
    def _base_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            {
                "HOOK_ADDRESS": "0x0000000000000000000000000000000000000003",
                "POOL_CURRENCY0": "0x0000000000000000000000000000000000000001",
                "POOL_CURRENCY1": "0x0000000000000000000000000000000000000002",
                "POOL_FEE": "3000",
                "POOL_TICK_SPACING": "60",
            }
        )
        return env

    def test_intent_create_json_dry_run(self) -> None:
        payload = {
            "token_in": "0x0000000000000000000000000000000000000001",
            "token_out": "0x0000000000000000000000000000000000000002",
            "amount_in": 1000000,
            "condition_type": "MAX_SLIPPAGE_BPS",
            "condition_value": 100,
            "expiry": 1893456000,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(payload, tmp)
            json_path = tmp.name

        try:
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "agent.cli.main",
                    "--json",
                    "intent",
                    "create",
                    "--json-file",
                    json_path,
                    "--dry-run",
                ],
                cwd=REPO_ROOT,
                env=self._base_env(),
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            output = json.loads(result.stdout.strip())
            self.assertEqual(output["status"], "dry_run")
            self.assertIn("validated_intent", output["details"])
        finally:
            os.unlink(json_path)

    def test_intent_create_text_missing_gemini_key(self) -> None:
        env = self._base_env()
        env.pop("GEMINI_API_KEY", None)

        result = subprocess.run(
            [
                "python3",
                "-m",
                "agent.cli.main",
                "--json",
                "intent",
                "create",
                "--text",
                "swap token0 to token1",
                "--dry-run",
            ],
            cwd=REPO_ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1, msg=result.stderr)
        output = json.loads(result.stdout.strip())
        self.assertEqual(output["status"], "error")
        self.assertIn("GEMINI_API_KEY", output["message"])


if __name__ == "__main__":
    unittest.main()

