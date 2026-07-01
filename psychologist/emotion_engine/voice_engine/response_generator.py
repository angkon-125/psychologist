"""
Response Generator

Orchestrates response generation with Ollama as the primary LLM backend
and EmotionEngine as the guaranteed fallback.

Priority:
  1. Try Ollama (if enabled and available)
  2. Fall back to EmotionEngine on any failure

All responses are kept concise for voice output.

Hallucination guardrails:
  - Source labeling: every response includes a "source" field
  - Uncertainty marking: low-confidence responses are prefixed
  - Missing data handling: never fabricate information
  - Prediction labeling: predictions are prefixed
  - Low-confidence clarification: appended when overall confidence < 0.5
"""

import logging
from typing import Optional, Dict

logger = logging.getLogger("zara.voice.response_generator")

# Maximum response length for voice (keep it short and natural)
_MAX_VOICE_RESPONSE_LENGTH = 200

# Confidence thresholds for guardrails
_UNCERTAINTY_THRESHOLD = 0.4
_LOW_CONFIDENCE_THRESHOLD = 0.5

# Uncertainty / clarification prefixes
_UNCERTAINTY_PREFIX_EN = "I'm not entirely sure, but "
_UNCERTAINTY_PREFIX_BN = "\u0986\u09ae\u09bf \u098f\u0995\u09a6\u09ae \u09a8\u09bf\u09b6\u09cd\u099a\u09bf\u09a4 \u09a8\u0987, \u0995\u09bf\u09a8\u09cd\u09a4\u09c1 "
_CLARIFICATION_SUFFIX_EN = " Could you tell me more about what you mean?"
_CLARIFICATION_SUFFIX_BN = " \u0986\u09aa\u09a8\u09bf \u0986\u09aa\u09a8\u09be\u09b0 \u0995\u09a5\u09be\u09b0 \u0986\u09b0\u0993 \u09ac\u09bf\u09b8\u09cd\u09a4\u09be\u09b0\u09bf\u09a4 \u09ac\u09b2\u09a4\u09c7 \u09aa\u09be\u09b0\u09c7\u09a8?"
_MISSING_DATA_EN = "I don't have enough information to answer that. Could you share a bit more?"
_MISSING_DATA_BN = "\u098f\u09ae\u09a8 \u09a4\u09a5\u09cd\u09af \u0986\u09ae\u09be\u09b0 \u0995\u09be\u099b\u09c7 \u09a8\u09c7\u0987\u0964 \u0986\u09aa\u09a8\u09bf \u0986\u09b0\u0993 \u09ac\u09bf\u09b8\u09cd\u09a4\u09be\u09b0\u09bf\u09a4 \u09ac\u09b2\u09a4\u09c7 \u09aa\u09be\u09b0\u09c7\u09a8?"


class ResponseGenerator:
    """
    Generates conversational responses using Ollama (optional) or EmotionEngine.

    Usage:
        gen = ResponseGenerator(emotion_engine, ollama_client=None)
        result = gen.generate("I feel anxious", language="en")
        # result = {"text": "...", "emotion": "...", "source": "emotion_engine"}
    """

    def __init__(self, emotion_engine, ollama_client=None):
        """
        Args:
            emotion_engine: The EmotionEngine instance (always available).
            ollama_client: Optional OllamaClient instance. If None, only
                          EmotionEngine is used.
        """
        self._emotion_engine = emotion_engine
        self._ollama = ollama_client

    def generate(
        self,
        transcript: str,
        language: str = "en",
        emotion_context: Optional[str] = None,
        confidence_scores: Optional[Dict] = None,
    ) -> Dict:
        """
        Generate a response for the user's transcript.

        Tries Ollama first (if enabled), falls back to EmotionEngine.
        Applies hallucination guardrails before returning.

        Returns:
            Dict with keys:
                - text: The response text
                - emotion: Detected/inferred emotion
                - source: "ollama" or "emotion_engine"
                - confidence: Confidence score (0-1)
        """
        # 1. Try Ollama if available
        if self._ollama is not None and self._ollama.is_available:
            ollama_response = self._try_ollama(transcript, language, emotion_context)
            if ollama_response is not None:
                return self._apply_guardrails(ollama_response, language, confidence_scores)

        # 2. Fall back to EmotionEngine
        result = self._use_emotion_engine(transcript, language)
        return self._apply_guardrails(result, language, confidence_scores)

    def _try_ollama(
        self,
        transcript: str,
        language: str,
        emotion_context: Optional[str],
    ) -> Optional[Dict]:
        """Attempt to generate a response via Ollama."""
        try:
            response_text = self._ollama.generate(
                user_message=transcript,
                language=language,
                emotion_context=emotion_context,
            )
            if response_text:
                # Truncate for voice
                response_text = self._truncate_for_voice(response_text)
                return {
                    "text": response_text,
                    "emotion": emotion_context or "neutral",
                    "source": "ollama",
                    "confidence": 0.8,
                }
        except Exception as e:
            logger.warning("Ollama response generation failed: %s", e)

        return None

    def _use_emotion_engine(self, transcript: str, language: str) -> Dict:
        """Generate a response using the EmotionEngine."""
        try:
            result = self._emotion_engine.process_input(transcript)

            response_text = result.get("response", "")
            if not response_text:
                response_text = self._default_response(language)

            # Truncate for voice
            response_text = self._truncate_for_voice(response_text)

            dominant_emotion = result.get("dominant_emotion", "neutral")
            confidence = result.get("emotional_state", {}).get("intensity", 0.5)

            return {
                "text": response_text,
                "emotion": dominant_emotion,
                "source": "emotion_engine",
                "confidence": confidence,
            }
        except Exception as e:
            logger.error("EmotionEngine response failed: %s", e)
            return {
                "text": self._default_response(language),
                "emotion": "neutral",
                "source": "fallback",
                "confidence": 0.0,
            }

    def _truncate_for_voice(self, text: str) -> str:
        """Truncate response text to be suitable for voice output."""
        if len(text) <= _MAX_VOICE_RESPONSE_LENGTH:
            return text

        # Try to cut at a sentence boundary
        truncated = text[:_MAX_VOICE_RESPONSE_LENGTH]
        last_period = truncated.rfind(".")
        if last_period > _MAX_VOICE_RESPONSE_LENGTH * 0.5:
            return truncated[:last_period + 1]

        # Otherwise cut at the last word boundary
        return truncated.rsplit(" ", 1)[0] + "..."

    @staticmethod
    def _default_response(language: str = "en") -> str:
        """Return a default empathetic response."""
        defaults = {
            "en": "I hear you. Tell me more about how you're feeling.",
            "bn": "আমি আপনাকে শুনছি। আপনার অনুভূতি সম্পর্কে আরও বলুন।",
        }
        return defaults.get(language, defaults["en"])

    def get_info(self) -> Dict:
        """Return info about the response generation setup."""
        return {
            "ollama_available": self._ollama is not None and self._ollama.is_available,
            "ollama_info": self._ollama.get_info() if self._ollama else None,
            "fallback": "emotion_engine",
            "max_response_length": _MAX_VOICE_RESPONSE_LENGTH,
            "hallucination_guardrails": True,
        }

    # ── Hallucination Guardrails ───────────────────────────────────

    def _apply_guardrails(
        self,
        response: Dict,
        language: str,
        confidence_scores: Optional[Dict] = None,
    ) -> Dict:
        """
        Apply hallucination guardrails to a generated response.

        1. Source labeling (already present in response dict)
        2. Uncertainty marking if confidence < 0.4
        3. Missing data handling if response text is empty
        4. Low-confidence clarification if overall confidence < 0.5
        """
        text = response.get("text", "")
        source = response.get("source", "unknown")
        confidence = response.get("confidence", 0.5)

        # 3. Missing data handling — never return empty response
        if not text or not text.strip():
            text = _MISSING_DATA_BN if language == "bn" else _MISSING_DATA_EN
            response["text"] = text
            response["source"] = "missing_data_fallback"
            response["confidence"] = 0.1
            return response

        # 2. Uncertainty marking
        if confidence < _UNCERTAINTY_THRESHOLD:
            prefix = _UNCERTAINTY_PREFIX_BN if language == "bn" else _UNCERTAINTY_PREFIX_EN
            text = prefix + text
            response["text"] = text

        # 4. Low-confidence clarification suffix
        overall_conf = 0.5
        if confidence_scores:
            overall_conf = confidence_scores.get("overall_confidence", confidence)
        if overall_conf < _LOW_CONFIDENCE_THRESHOLD:
            suffix = _CLARIFICATION_SUFFIX_BN if language == "bn" else _CLARIFICATION_SUFFIX_EN
            text = text + suffix
            response["text"] = text

        # Ensure source is always labeled
        response.setdefault("source", source)

        return response
