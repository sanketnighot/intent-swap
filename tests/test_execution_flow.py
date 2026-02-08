import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from web3.exceptions import TransactionNotFound

from agent.execution_engine import run_single_pass


class _FakeEth:
    def __init__(self) -> None:
        self.receipts: dict[str, SimpleNamespace] = {}

    def get_transaction_receipt(self, tx_hash: str) -> SimpleNamespace:
        if tx_hash in self.receipts:
            return self.receipts[tx_hash]
        raise TransactionNotFound(f"missing: {tx_hash}")


class _FakeW3:
    def __init__(self) -> None:
        self.eth = _FakeEth()


class _FakeRuntime:
    def __init__(self) -> None:
        self.w3 = _FakeW3()
        self.poll_interval_ms = 15000
        self.pool_key = {}
        self.swap_target = object()
        self.account = object()


def _pending_intent() -> dict[str, object]:
    return {
        "user": "0x0000000000000000000000000000000000000009",
        "tokenIn": "0x0000000000000000000000000000000000000001",
        "tokenOut": "0x0000000000000000000000000000000000000002",
        "amountIn": 1000,
        "conditionType": 1,
        "conditionValue": 100,
        "expiry": 1893456000,
        "executed": False,
        "poolId": b"\x00" * 32,
        "zeroForOne": True,
        "referenceSqrtPriceX96": 1,
    }


def _executed_intent() -> dict[str, object]:
    data = _pending_intent()
    data["executed"] = True
    return data


class ExecutionFlowTests(unittest.TestCase):
    def test_submit_then_confirm_next_pass(self) -> None:
        runtime = _FakeRuntime()
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, "state.json")
            with patch.dict(os.environ, {"EXECUTOR_STATE_FILE": state_path}, clear=False):
                with patch("agent.execution_engine.create_runtime_clients", return_value=runtime):
                    with patch("agent.execution_engine.get_intent_count", return_value=1):
                        with patch("agent.execution_engine.get_intent", return_value=_pending_intent()):
                            with patch("agent.execution_engine.can_execute_intent", return_value=True):
                                with patch("agent.execution_engine.send_swap", return_value="0xtx1"):
                                    summary = run_single_pass(dry_run=False)
                                    self.assertEqual(summary["submitted"], 1)
                                    self.assertEqual(summary["confirmed"], 0)

                runtime.w3.eth.receipts["0xtx1"] = SimpleNamespace(status=1, blockNumber=123)
                with patch("agent.execution_engine.create_runtime_clients", return_value=runtime):
                    with patch("agent.execution_engine.get_intent_count", return_value=1):
                        with patch("agent.execution_engine.get_intent", return_value=_executed_intent()):
                            with patch("agent.execution_engine.can_execute_intent", return_value=False):
                                with patch("agent.execution_engine.send_swap", return_value="0xtx2"):
                                    summary = run_single_pass(dry_run=False)
                                    self.assertEqual(summary["confirmed"], 1)
                                    self.assertEqual(summary["submitted"], 0)
                                    self.assertEqual(summary["skipped_executed"], 1)

    def test_dry_run_executable_no_submission(self) -> None:
        runtime = _FakeRuntime()
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, "state.json")
            with patch.dict(os.environ, {"EXECUTOR_STATE_FILE": state_path}, clear=False):
                with patch("agent.execution_engine.create_runtime_clients", return_value=runtime):
                    with patch("agent.execution_engine.get_intent_count", return_value=1):
                        with patch("agent.execution_engine.get_intent", return_value=_pending_intent()):
                            with patch("agent.execution_engine.can_execute_intent", return_value=True):
                                with patch("agent.execution_engine.send_swap", return_value="0xtx1") as mocked_send:
                                    summary = run_single_pass(dry_run=True)
                                    self.assertEqual(summary["dry_run_executable"], 1)
                                    self.assertEqual(summary["submitted"], 0)
                                    mocked_send.assert_not_called()

    def test_pending_inflight_skips_duplicate_submission(self) -> None:
        runtime = _FakeRuntime()
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = os.path.join(tmpdir, "state.json")
            os.environ["EXECUTOR_STATE_FILE"] = state_path

            # First pass submits and records inflight tx.
            with patch("agent.execution_engine.create_runtime_clients", return_value=runtime):
                with patch("agent.execution_engine.get_intent_count", return_value=1):
                    with patch("agent.execution_engine.get_intent", return_value=_pending_intent()):
                        with patch("agent.execution_engine.can_execute_intent", return_value=True):
                            with patch("agent.execution_engine.send_swap", return_value="0xtx1"):
                                run_single_pass(dry_run=False)

            # Second pass should observe pending inflight and skip submission.
            with patch("agent.execution_engine.create_runtime_clients", return_value=runtime):
                with patch("agent.execution_engine.get_intent_count", return_value=1):
                    with patch("agent.execution_engine.get_intent", return_value=_pending_intent()):
                        with patch("agent.execution_engine.can_execute_intent", return_value=True):
                            with patch("agent.execution_engine.send_swap", return_value="0xtx2") as mocked_send:
                                summary = run_single_pass(dry_run=False)
                                self.assertEqual(summary["inflight_pending"], 1)
                                self.assertEqual(summary["skipped_inflight"], 1)
                                self.assertEqual(summary["submitted"], 0)
                                mocked_send.assert_not_called()


if __name__ == "__main__":
    unittest.main()

