"""
Ollama Client (Optional LLM Backend)

Provides an optional local LLM backend via Ollama.
Only activated when USE_OLLAMA=true environment variable is set.
Gracefully degrades: returns None on any error, timeout, or unavailability.

All communication is local/offline — no cloud API calls.
"""

import os
import logging
from typing import Optional, Dict, List

logger = logging.getLogger("zara.voice.ollama")

# Default system prompt for empathetic psychological support
_DEFAULT_SYSTEM_PROMPT = (
    "You are ZARA, an offline AI emotional support companion. "
    "You are warm, empathetic, and non-judgmental. "
    "You listen carefully and respond with understanding. "
    "You help users process their emotions, think through problems, "
    "and feel supported. Keep responses concise and natural for voice — "
    "no more than 2-3 sentences. Never claim to be a therapist or "
    "replace professional help. If the user seems in crisis, gently "
    "suggest reaching out to a local professional helpline."
)


class OllamaClient:
    """
    Optional local LLM client via Ollama HTTP API.

    Usage:
        client = OllamaClient()  # Only succeeds if Ollama is running
        response = client.generate("I feel anxious today")
        if response is None:
            # Fall back to EmotionEngine
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 5.0,
        system_prompt: Optional[str] = None,
    ):
        self._base_url = (
            base_url
            or os.environ.get("OLLAMA_URL", "http://localhost:11434")
        )
        self._model = (
            model
            or os.environ.get("OLLAMA_MODEL", "llama3.2")
        )
        self._timeout = timeout_seconds
        self._system_prompt = system_prompt or _DEFAULT_SYSTEM_PROMPT
        self._available = False
        self._conversation_history: List[Dict] = []

        # Verify Ollama is reachable
        self._check_availability()

    def _check_availability(self):
        """Check if Ollama is running and the model is available."""
        try:
            import httpx
            resp = httpx.get(
                f"{self._base_url}/api/tags",
                timeout=2.0,
            )
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                # Check if our model (or a compatible one) exists
                if any(self._model in m for m in model_names):
                    self._available = True
                    logger.info("Ollama available with model: %s", self._model)
                else:
                    logger.warning(
                        "Ollama running but model '%s' not found. Available: %s",
                        self._model, model_names,
                    )
                    # Try to use whatever model is available
                    if model_names:
                        self._model = model_names[0]
                        self._available = True
                        logger.info("Falling back to available model: %s", self._model)
            else:
                logger.warning("Ollama returned status %d", resp.status_code)
        except ImportError:
            logger.warning("httpx not installed. Ollama client unavailable.")
        except Exception as e:
            logger.info("Ollama not reachable: %s", e)

    @property
    def is_available(self) -> bool:
        return self._available

    def generate(
        self,
        user_message: str,
        language: str = "en",
        emotion_context: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a response using Ollama.

        Returns the response text, or None if Ollama is unavailable,
        timed out, or returned an error.
        """
        if not self._available:
            return None

        try:
            import httpx

            # Build the prompt with emotion context
            prompt = user_message
            if emotion_context:
                prompt = f"[User's emotional state: {emotion_context}]\n\n{user_message}"

            # Add conversation history for context
            self._conversation_history.append({
                "role": "user",
                "content": user_message,
            })

            # Keep history manageable (last 10 turns)
            if len(self._conversation_history) > 20:
                self._conversation_history = self._conversation_history[-20:]

            resp = httpx.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": self._system_prompt},
                        *self._conversation_history,
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 150,  # Keep responses short for voice
                    },
                },
                timeout=self._timeout,
            )

            if resp.status_code == 200:
                data = resp.json()
                message = data.get("message", {})
                response_text = message.get("content", "").strip()

                if response_text:
                    # Add to history
                    self._conversation_history.append({
                        "role": "assistant",
                        "content": response_text,
                    })
                    return response_text
                else:
                    logger.warning("Ollama returned empty response")
                    return None
            else:
                logger.warning("Ollama returned status %d", resp.status_code)
                return None

        except Exception as e:
            logger.warning("Ollama generation failed: %s", e)
            self._available = False  # Mark as unavailable for future calls
            return None

    def reset_conversation(self):
        """Clear conversation history."""
        self._conversation_history.clear()

    def get_info(self) -> Dict:
        """Return client info for debugging."""
        return {
            "available": self._available,
            "base_url": self._base_url,
            "model": self._model,
            "timeout_seconds": self._timeout,
            "history_length": len(self._conversation_history),
        }
