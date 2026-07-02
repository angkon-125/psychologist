"""
Shared active Orchestrator Agent instance for API routing blueprints.
"""

from backend.agent.orchestrator import OrchestratorAgent
from backend.safety.safety_agent import SafetyAgent
from backend.llm.llm_agent import LLMAgent
from backend.memory.memory_agent import MemoryAgent
from backend.psychologist.psychologist_agent import PsychologistAgent
from backend.voice.voice_agent import VoiceAgent
from backend.tools.tool_agent import ToolAgent
from backend.prediction.prediction_agent import PredictionAgent
from backend.evaluation.evaluation_agent import EvaluationAgent

# Global Orchestrator instance
orchestrator = OrchestratorAgent()

def initialize_system() -> OrchestratorAgent:
    """Initializes the multi-agent system and registers all specialist agents."""
    global orchestrator
    
    # 1. Instantiate agents
    safety = SafetyAgent()
    llm = LLMAgent()
    memory = MemoryAgent()
    psychologist = PsychologistAgent()
    voice = VoiceAgent()
    tool = ToolAgent()
    prediction = PredictionAgent()
    evaluation = EvaluationAgent()
    
    # 2. Initialize them
    safety.initialize()
    llm.initialize()
    memory.initialize()
    psychologist.initialize()
    voice.initialize()
    tool.initialize()
    prediction.initialize()
    evaluation.initialize()
    
    # 3. Register with Orchestrator
    orchestrator.register_specialist("safety", safety)
    orchestrator.register_specialist("llm", llm)
    orchestrator.register_specialist("memory", memory)
    orchestrator.register_specialist("psychologist", psychologist)
    orchestrator.register_specialist("voice", voice)
    orchestrator.register_specialist("tool", tool)
    orchestrator.register_specialist("prediction", prediction)
    orchestrator.register_specialist("evaluation", evaluation)
    
    orchestrator.initialize()
    return orchestrator
