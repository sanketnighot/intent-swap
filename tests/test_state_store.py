import os
import tempfile
import unittest

from agent.state_store import StateStore


class StateStoreTests(unittest.TestCase):
    def test_roundtrip_inflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "state.json")
            store = StateStore(path)
            store.set_inflight(7, "0xabc", submitted_at=1700000000)
            store.save()

            reloaded = StateStore(path)
            self.assertTrue(reloaded.has_inflight(7))
            item = reloaded.get_inflight(7)
            self.assertIsNotNone(item)
            assert item is not None
            self.assertEqual(item.tx_hash, "0xabc")
            self.assertEqual(item.submitted_at, 1700000000)

            reloaded.clear_inflight(7)
            reloaded.save()
            final = StateStore(path)
            self.assertFalse(final.has_inflight(7))

    def test_get_inflight_ids_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "state.json")
            store = StateStore(path)
            store.set_inflight(9, "0x9")
            store.set_inflight(2, "0x2")
            store.set_inflight(5, "0x5")
            self.assertEqual(store.get_inflight_ids(), [2, 5, 9])


if __name__ == "__main__":
    unittest.main()

