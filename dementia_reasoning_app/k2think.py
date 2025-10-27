"""Mock interface for the K2 Think reasoning engine."""

from __future__ import annotations

import re

from .scoreboard import ReasoningResult


class K2ThinkClient:
    """Deterministic mock of a clinical reasoning model."""

    _POSITIVE_KEYWORDS = {
        "remember": 5,
        "family": 3,
        "doctor": 4,
        "garden": 2,
        "exercise": 4,
        "today": 1,
        "yesterday": 2,
        "morning": 1,
        "appointment": 3,
    }

    _NEGATIVE_KEYWORDS = {
        "confused": -5,
        "lost": -4,
        "forget": -3,
        "pain": -2,
        "anxious": -3,
        "tired": -1,
        "worried": -2,
    }

    def run_reasoning(self, transcript: str) -> ReasoningResult:
        """Generate a structured reasoning response from a transcript."""

        normalized = transcript.lower()
        keyword_score = self._calculate_keyword_score(normalized)
        length_factor = min(len(transcript.split()) / 40.0, 1.0)
        coherence = self._score_from_pattern(normalized)
        orientation = self._score_orientation(normalized)
        memory_recall = min(60 + keyword_score * 4 + length_factor * 25, 100)
        language = min(55 + coherence * 30 + length_factor * 20, 100)

        overall = max(
            0.0,
            min(100.0, (memory_recall + language + orientation * 100 + coherence * 100) / 4),
        )

        reasoning_chain = [
            "Interpreting patient narrative for memory cues",
            "Evaluating linguistic structure and orientation markers",
            "Synthesizing a supportive clinical response",
        ]

        response = self._compose_response(transcript, overall, orientation)
        insights = self._compose_insights(overall, orientation, memory_recall)

        metrics = {
            "coherence": round(coherence * 100, 2),
            "memory_recall": round(memory_recall, 2),
            "orientation": round(orientation * 100, 2),
            "language": round(language, 2),
        }

        return ReasoningResult(
            response=response,
            reasoning_chain=reasoning_chain,
            overall_score=round(overall, 2),
            metrics=metrics,
            insights=insights,
        )

    # ------------------------------------------------------------------
    def _calculate_keyword_score(self, normalized: str) -> float:
        score = 0
        for keyword, weight in self._POSITIVE_KEYWORDS.items():
            if keyword in normalized:
                score += weight
        for keyword, weight in self._NEGATIVE_KEYWORDS.items():
            if keyword in normalized:
                score += weight
        return score

    def _score_from_pattern(self, normalized: str) -> float:
        sentences = re.split(r"[.!?]+", normalized)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0.3
        average_length = sum(len(s.split()) for s in sentences) / len(sentences)
        return max(0.3, min(1.0, average_length / 15.0))

    def _score_orientation(self, normalized: str) -> float:
        orientation_markers = 0
        if re.search(r"\b(today|yesterday|tomorrow|morning|afternoon|evening)\b", normalized):
            orientation_markers += 1
        if re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", normalized):
            orientation_markers += 1
        if re.search(r"\b(home|clinic|hospital|park|store)\b", normalized):
            orientation_markers += 1
        return min(1.0, 0.35 + orientation_markers * 0.2)

    def _compose_response(self, transcript: str, overall: float, orientation: float) -> str:
        if overall > 75:
            tone = "You're demonstrating strong clarity and recall."
        elif overall > 55:
            tone = "I appreciate the details you're sharing."
        else:
            tone = "Thank you for sharing that with me."

        orientation_feedback = (
            "It sounds like you're oriented to time and place."
            if orientation > 0.6
            else "Let's keep working together on situational details."
        )

        return (
            f"{tone} You mentioned '{transcript}'. {orientation_feedback} "
            "Is there anything else you'd like to talk through?"
        )

    def _compose_insights(self, overall: float, orientation: float, memory_recall: float) -> str:
        flags = []
        if overall < 50:
            flags.append("Monitor for disorientation cues")
        if memory_recall < 60:
            flags.append("Memory recall support recommended")
        if orientation < 0.5:
            flags.append("Follow-up orientation assessment suggested")

        if not flags:
            return "No clinical alerts raised. Continue routine monitoring."
        return "; ".join(flags)


__all__ = ["K2ThinkClient"]
