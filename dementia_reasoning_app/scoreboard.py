"""Scoreboard utilities for tracking reasoning metrics over time."""

from __future__ import annotations

import statistics
import typing as t
from dataclasses import dataclass
from datetime import datetime
from threading import Lock


@dataclass
class ReasoningResult:
    """Normalized reasoning response returned by the K2 Think client."""

    response: str
    reasoning_chain: list[str]
    overall_score: float
    metrics: dict[str, float]
    insights: str


class ReasoningScoreboard:
    """Track and aggregate reasoning metrics for clinician dashboards."""

    def __init__(self) -> None:
        self._history: list[dict[str, t.Any]] = []
        self._lock = Lock()

    # ------------------------------------------------------------------
    def record_interaction(
        self, transcript: str, reasoning_result: ReasoningResult
    ) -> dict[str, t.Any]:
        timestamp = datetime.utcnow().isoformat() + "Z"
        entry = {
            "timestamp": timestamp,
            "transcript": transcript,
            "response": reasoning_result.response,
            "score": reasoning_result.overall_score,
            "metrics": reasoning_result.metrics,
            "insights": reasoning_result.insights,
        }

        with self._lock:
            self._history.append(entry)

        return entry

    # ------------------------------------------------------------------
    def export(self) -> dict[str, t.Any]:
        with self._lock:
            history_copy = list(self._history)

        if not history_copy:
            return {
                "history": [],
                "averages": {},
                "latest": None,
            }

        metrics_keys = set().union(*(entry["metrics"].keys() for entry in history_copy))
        averages = {
            metric: round(
                statistics.mean(entry["metrics"].get(metric, 0.0) for entry in history_copy),
                2,
            )
            for metric in metrics_keys
        }

        averages["score"] = round(statistics.mean(entry["score"] for entry in history_copy), 2)
        averages.setdefault("overall", averages["score"])

        return {
            "history": history_copy,
            "averages": averages,
            "latest": history_copy[-1],
        }


__all__ = ["ReasoningScoreboard", "ReasoningResult"]
