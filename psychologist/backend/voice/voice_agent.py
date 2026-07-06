"""
Voice Agent

Responsible for state machine management, microphone capture, VAD, pause detection,
partial transcripts, barge-in detection, and playback coordination.
"""

from typing import Dict, Any

from backend.agent.base import BaseAgent
from backend.agent.schemas import AgentRequest, AgentResponse
from .state_machine import VoiceStateMachine, VoiceState
from .vad import VoiceActivityDetector
from .pause_detector import SmartPauseDetector
from .transcript_manager import TranscriptManager
from .playback_controller import PlaybackController
from .echo_guard import EchoGuard

class VoiceAgent(BaseAgent):
    """
    Voice Agent coordinates microphone input, VAD processing, pause detection,
    and voice playbacks.
    """

    def __init__(self):
        super().__init__()
        self.state_machine = VoiceStateMachine()
        self.vad = None
        self.pause_detector = None
        self.transcripts = None
        self.playback = None
        self.echo_guard = None

    def _get_agent_name(self) -> str:
        return "voice"

    def initialize(self) -> bool:
        self.vad = VoiceActivityDetector()
        self.pause_detector = SmartPauseDetector()
        self.transcripts = TranscriptManager()
        self.playback = PlaybackController()
        self.echo_guard = EchoGuard()
        self._initialized = True
        return True

    def process(self, request: AgentRequest) -> AgentResponse:
        purpose = request.metadata.get("purpose", "get_state")
        
        if purpose == "get_state":
            current_state = self.state_machine.state.name
            return AgentResponse(
                success=True,
                agent=self.name,
                response=f"Voice state is {current_state}",
                metadata={"state": current_state}
            )
            
        elif purpose == "transition":
            to_state_str = request.metadata.get("to_state", "")
            reason = request.metadata.get("reason", "")
            try:
                to_state = VoiceState[to_state_str]
                success = self.state_machine.transition_to(to_state, reason=reason)
                return AgentResponse(
                    success=success,
                    agent=self.name,
                    response=f"Transition to {to_state_str} success={success}",
                    metadata={"state": self.state_machine.state.name}
                )
            except KeyError:
                return AgentResponse.error(self.name, f"Invalid voice state: {to_state_str}")

        elif purpose == "speak":
            text_to_speak = request.text
            language = request.language
            self.state_machine.transition_to(VoiceState.SPEAKING, "Playing response")
            # Arm echo guard before TTS starts
            if self.echo_guard:
                self.echo_guard.arm(text_to_speak)
            success = self.playback.speak(text_to_speak, language=language)
            # Disarm echo guard after TTS finishes
            if self.echo_guard:
                self.echo_guard.disarm()
            self.state_machine.transition_to(VoiceState.IDLE, "Playback finished")
            return AgentResponse(
                success=success,
                agent=self.name,
                response="Spoken successfully" if success else "Playback failed"
            )

        elif purpose == "echo_check":
            fragment = request.text
            is_echo = self.echo_guard.is_echo(fragment) if self.echo_guard else False
            return AgentResponse(
                success=True,
                agent=self.name,
                response="echo" if is_echo else "speech",
                metadata={"is_echo": is_echo, "echo_guard_armed": self.echo_guard.is_armed if self.echo_guard else False}
            )

        elif purpose == "stop_playback":
            self.playback.stop()
            self.state_machine.transition_to(VoiceState.IDLE, "Interrupted")
            return AgentResponse(success=True, agent=self.name, response="Playback stopped")

        return AgentResponse.error(self.name, f"Unknown voice agent purpose: {purpose}")
