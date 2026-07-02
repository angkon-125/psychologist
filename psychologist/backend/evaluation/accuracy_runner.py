"""
Accuracy Runner

Wraps the legacy AccuracyEvaluator to run test suites and capture performance metrics.
"""

import sys
from pathlib import Path
from typing import Dict, Any

_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from evaluation.accuracy_evaluator import AccuracyEvaluator

class AccuracyRunner:
    """Runs legacy evaluation scenarios."""

    def __init__(self):
        # We need mock or actual objects for the legacy constructor
        # evaluator = AccuracyEvaluator(emotion_engine, safety_layer, text_handler)
        from emotion_engine.emotion_engine import EmotionEngine
        from emotion_engine.interaction.safety_support_layer import SafetySupportLayer
        from emotion_engine.interaction.text_mode_handler import TextModeHandler
        
        self.engine = EmotionEngine()
        self.safety = SafetySupportLayer()
        self.handler = TextModeHandler(self.engine, safety_layer=self.safety)
        
        # Path to existing evaluation/ folder
        eval_path = _project_root / "psychologist" / "evaluation"
        if not eval_path.exists():
            eval_path = _project_root / "evaluation"
            
        self.evaluator = AccuracyEvaluator(
            emotion_engine=self.engine,
            safety_layer=self.safety,
            text_handler=self.handler,
            eval_dir=str(eval_path)
        )

    def run(self) -> Dict[str, Any]:
        return self.evaluator.run_all()
