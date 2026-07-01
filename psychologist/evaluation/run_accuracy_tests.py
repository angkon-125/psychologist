"""
ZARA Accuracy Evaluation — CLI Entry Point

Run via:
    python -m evaluation.run_accuracy_tests

Initializes the EmotionEngine + SafetySupportLayer, runs
AccuracyEvaluator.run_all(), prints a console report, and saves
a JSON report to logs/accuracy_report.json.

Exit code 0 if all targets met, 1 otherwise.
"""

import sys
import os
import io
import logging

# Ensure project root is on sys.path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from emotion_engine import EmotionEngine
from emotion_engine.interaction.safety_support_layer import SafetySupportLayer
from emotion_engine.interaction.text_mode_handler import TextModeHandler

from evaluation.accuracy_evaluator import AccuracyEvaluator
from evaluation.report_generator import ReportGenerator

logger = logging.getLogger("zara.evaluation")


def main():
    """Run the accuracy evaluation suite."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    # Ensure stdout can handle unicode
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("\n  Initializing ZARA components for evaluation...\n")

    # Initialize pipeline components
    emotion_engine = EmotionEngine()
    safety_layer = SafetySupportLayer()
    text_handler = TextModeHandler(
        emotion_engine=emotion_engine,
        tts_manager=None,
        safety_layer=safety_layer,
    )

    # Run evaluation
    evaluator = AccuracyEvaluator(
        emotion_engine=emotion_engine,
        safety_layer=safety_layer,
        text_handler=text_handler,
    )

    results = evaluator.run_all()

    # Generate reports
    report_gen = ReportGenerator()

    # Console report
    console_report = report_gen.generate_console_report(results)
    print(console_report)

    # JSON report
    report_gen.generate_json_report(results)
    print("  JSON report saved to logs/accuracy_report.json\n")

    # Exit code
    if results.get("all_targets_met"):
        print("  Result: ALL TARGETS MET [PASS]\n")
        return 0
    else:
        print("  Result: SOME TARGETS NOT MET [FAIL]\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
