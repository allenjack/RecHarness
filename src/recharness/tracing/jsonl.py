"""JSONL trace logger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from recharness.schema import TraceEvent


class JsonlTraceLogger:
    """Append RecHarness trace events to a JSONL file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        trace_id: str,
        step: int,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> TraceEvent:
        event = TraceEvent(
            trace_id=trace_id,
            step=step,
            event_type=event_type,
            payload=payload or {},
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return event
