from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TraceRecorder:
    def __init__(
        self,
        trace_path: Path,
        run_id: str,
        agent_name: str,
    ) -> None:
        self.trace_path = trace_path
        self.run_id = run_id
        self.agent_name = agent_name
        self.step = 0

        self.trace_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def record(
        self,
        event_type: str,
        content: Any,
        *,
        tool_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.step += 1

        event = {
            "run_id": self.run_id,
            "step": self.step,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "agent": self.agent_name,
            "event_type": event_type,
            "tool_name": tool_name,
            "content": content,
            "metadata": metadata or {},
        }

        with self.trace_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    event,
                    ensure_ascii=False,
                )
                + "\n"
            )
