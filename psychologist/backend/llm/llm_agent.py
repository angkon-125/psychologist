"""
LLM Agent

Responsible for constructing system prompts, query generation via local Ollama LLM,
and routing back to the EmotionEngine fallback when Ollama is unavailable or timed out.
"""

from typing import Dict, Any, Optional

from backend.agent.base import BaseAgent
from backend.agent.schemas import AgentRequest, AgentResponse
from backend.config import config
from .ollama_client import OllamaClient
from .emotion_engine_adapter import EmotionEngineAdapter
from .prompts import SYSTEM_PROMPT_EN, SYSTEM_PROMPT_BN

class LLMAgent(BaseAgent):
    """
    LLM Agent orchestrates local LLM generation and handles timeout or failure.
    If Ollama is disabled or unreachable, it falls back seamlessly to EmotionEngine.
    """

    def __init__(self):
        super().__init__()
        self._ollama_client = None
        self._emotion_engine = None

    def _get_agent_name(self) -> str:
        return "llm"

    def initialize(self) -> bool:
        # Initialize adapter
        self._emotion_engine = EmotionEngineAdapter()
        
        # Optionally initialize Ollama client if enabled
        if config.USE_OLLAMA:
            try:
                self._ollama_client = OllamaClient(
                    base_url=config.OLLAMA_BASE_URL,
                    model=config.DEFAULT_MODEL,
                    timeout_seconds=config.OLLAMA_TIMEOUT_SECONDS
                )
                self._logger.info("OllamaClient initialized: available=%s", self._ollama_client.is_available)
            except Exception as e:
                self._logger.warning("Ollama connection failed: %s. Falling back to EmotionEngine.", e)
                self._ollama_client = None
        else:
            self._logger.info("Ollama disabled via config. Using EmotionEngine as primary.")
        
        self._initialized = True
        return True

    def process(self, request: AgentRequest) -> AgentResponse:
        text = request.text
        language = request.language
        context = request.metadata.get("context", "")
        
        # 1. Attempt local Ollama generation if available
        fallback_used = False
        response_text = ""
        confidence = 0.8
        dominant_emotion = "neutral"
        
        if self._ollama_client and self._ollama_client.is_available:
            self._logger.info("Attempting response generation via Ollama...")
            emotion_ctx = request.user_mood or "neutral"
            prompt_context = f"Context history:\n{context}\nUser current message: {text}"
            
            try:
                # Set dynamic system prompt based on language
                system_prompt = SYSTEM_PROMPT_BN if language == "bn" else SYSTEM_PROMPT_EN
                self._ollama_client._system_prompt = system_prompt
                
                response_text = self._ollama_client.generate(
                    user_message=prompt_context,
                    language=language,
                    emotion_context=emotion_ctx
                )
            except Exception as e:
                self._logger.warning("Ollama execution failed: %s. Falling back.", e)
                response_text = None
            
            if not response_text:
                fallback_used = True
                self._logger.info("Ollama failed or returned empty response. Falling back to EmotionEngine.")
        else:
            fallback_used = True

        # 2. Fallback to EmotionEngine
        if fallback_used:
            self._logger.info("Generating response via EmotionEngine...")
            result = self._emotion_engine.process(text, language)
            response_text = result["response"]
            dominant_emotion = result["dominant_emotion"]
            confidence = result["confidence"]
            
        return AgentResponse(
            success=True,
            agent=self.name,
            intent=request.metadata.get("intent", "general"),
            response=response_text,
            confidence=confidence,
            risk_level="low",
            metadata={
                "fallback_used": fallback_used,
                "dominant_emotion": dominant_emotion,
                "model": config.DEFAULT_MODEL if not fallback_used else "emotion_engine"
            }
        )
