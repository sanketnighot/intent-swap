import os
import unittest
from unittest.mock import patch

from agent.execution_engine import load_engine_config


class ExecutionEngineConfigTests(unittest.TestCase):
    def test_load_defaults(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            cfg = load_engine_config(default_interval_ms=15000, interval_override=None)
            self.assertEqual(cfg.interval_ms, 15000)
            self.assertEqual(cfg.retry_attempts, 3)
            self.assertEqual(cfg.retry_delay_ms, 500)
            self.assertEqual(cfg.inflight_ttl_sec, 600)

    def test_invalid_retry_attempts_raises(self) -> None:
        with patch.dict(os.environ, {"EXECUTOR_RETRY_ATTEMPTS": "0"}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "must be > 0"):
                load_engine_config(default_interval_ms=15000, interval_override=None)

    def test_interval_override(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            cfg = load_engine_config(default_interval_ms=15000, interval_override=5000)
            self.assertEqual(cfg.interval_ms, 5000)


if __name__ == "__main__":
    unittest.main()

