import json
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class InflightTx:
    tx_hash: str
    submitted_at: int

    def to_dict(self) -> dict[str, Any]:
        return {"tx_hash": self.tx_hash, "submitted_at": self.submitted_at}


class StateStore:
    def __init__(self, path: str) -> None:
        self.path = path
        self._state: dict[str, Any] = {"version": 1, "inflight": {}}
        self.load()

    def load(self) -> None:
        if not os.path.exists(self.path):
            return

        with open(self.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        inflight = data.get("inflight", {})
        if not isinstance(inflight, dict):
            raise RuntimeError("state file inflight section must be an object")

        self._state = {"version": int(data.get("version", 1)), "inflight": inflight}

    def save(self) -> None:
        directory = os.path.dirname(self.path)
        if directory != "":
            os.makedirs(directory, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(prefix=".intentswap-state-", suffix=".json", dir=directory or ".")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self._state, handle, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(tmp_path, self.path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def get_inflight_ids(self) -> list[int]:
        ids: list[int] = []
        for raw_key in self._state["inflight"].keys():
            try:
                ids.append(int(raw_key))
            except ValueError:
                continue
        return sorted(ids)

    def has_inflight(self, intent_id: int) -> bool:
        return str(intent_id) in self._state["inflight"]

    def get_inflight(self, intent_id: int) -> InflightTx | None:
        raw = self._state["inflight"].get(str(intent_id))
        if raw is None:
            return None
        return InflightTx(tx_hash=str(raw["tx_hash"]), submitted_at=int(raw["submitted_at"]))

    def set_inflight(self, intent_id: int, tx_hash: str, submitted_at: int | None = None) -> None:
        self._state["inflight"][str(intent_id)] = InflightTx(
            tx_hash=tx_hash,
            submitted_at=int(time.time()) if submitted_at is None else int(submitted_at),
        ).to_dict()

    def clear_inflight(self, intent_id: int) -> None:
        self._state["inflight"].pop(str(intent_id), None)
