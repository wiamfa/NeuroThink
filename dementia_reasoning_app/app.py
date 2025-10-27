"""Application wiring for the DementiaReasoningApp Flask project."""

from __future__ import annotations

import typing as t
from datetime import datetime

from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO, emit

from .k2think import K2ThinkClient
from .scoreboard import ReasoningScoreboard


class DementiaReasoningApp:
    """Configure and run the dementia reasoning demo application."""

    def __init__(self, import_name: str | None = None) -> None:
        self.flask_app = Flask(import_name or __name__)
        self.flask_app.config.setdefault("SECRET_KEY", "dementia-reasoning-secret")

        self.socketio = SocketIO(
            self.flask_app, async_mode="eventlet", cors_allowed_origins="*"
        )

        self._k2_client = K2ThinkClient()
        self._scoreboard = ReasoningScoreboard()

        self._register_routes()
        self._register_socket_handlers()

    # ------------------------------------------------------------------
    # Flask wiring
    # ------------------------------------------------------------------
    def _register_routes(self) -> None:
        app = self.flask_app

        @app.route("/")
        def patient_view() -> str:
            return render_template("patient.html")

        @app.route("/clinician")
        def clinician_view() -> str:
            return render_template("clinician.html")

        @app.route("/api/scoreboard", methods=["GET"])
        def scoreboard_snapshot() -> t.Tuple[t.Any, int]:
            return jsonify(self._scoreboard.export()), 200

    def _register_socket_handlers(self) -> None:
        socketio = self.socketio

        @socketio.on("connect")
        def handle_connect() -> None:  # pragma: no cover - runtime callback
            emit("clinician_update", self._scoreboard.export())

        @socketio.on("patient_message")
        def handle_patient_message(data: dict[str, t.Any]) -> None:
            transcript = (data or {}).get("transcript", "").strip()
            if not transcript:
                emit(
                    "assistant_response",
                    {
                        "response": "I didn't catch that. Could you please repeat your thoughts?",
                        "reasoning": [],
                        "score": None,
                        "metrics": {},
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    },
                )
                return

            reasoning_result = self._k2_client.run_reasoning(transcript)
            interaction = self._scoreboard.record_interaction(
                transcript, reasoning_result
            )

            emit(
                "assistant_response",
                {
                    "response": reasoning_result.response,
                    "reasoning": reasoning_result.reasoning_chain,
                    "score": reasoning_result.overall_score,
                    "metrics": reasoning_result.metrics,
                    "timestamp": interaction["timestamp"],
                    "insights": reasoning_result.insights,
                },
            )

            socketio.emit("clinician_update", self._scoreboard.export())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, host: str = "0.0.0.0", port: int = 5000, **kwargs: t.Any) -> None:
        """Run the development server using Flask-SocketIO."""

        self.socketio.run(self.flask_app, host=host, port=port, **kwargs)


__all__ = ["DementiaReasoningApp"]
