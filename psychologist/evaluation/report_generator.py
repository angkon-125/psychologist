"""
Report Generator

Generates console and JSON reports from accuracy evaluation results.
Includes per-category accuracy, pass/fail status, and improvement
recommendations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("zara.evaluation.report")

# Category display names
_CATEGORY_NAMES = {
    "stt_accuracy": "Speech Recognition",
    "intent_classification": "Intent Detection",
    "safety_detection": "Safety Detection",
    "tool_routing": "Tool Routing",
    "response_relevance": "Response Quality",
    "fallback_reliability": "Fallback Reliability",
    "voice_processing": "Voice Processing",
}

# Recommendation templates per category
_RECOMMENDATIONS = {
    "stt_accuracy": [
        "Consider updating VAD noise threshold for noisy environments.",
        "Check if STT engine model needs retraining on domain-specific vocabulary.",
        "Verify audio sample rate matches STT engine expectations.",
    ],
    "intent_classification": [
        "Review emotion engine keyword mappings for missed intents.",
        "Add more training examples for underperforming intent categories.",
        "Consider adding context-aware intent disambiguation.",
    ],
    "safety_detection": [
        "Update crisis keyword lists with newly identified phrases.",
        "Review false negatives — some crisis language may be missed.",
        "Check Bangla keyword coverage for safety-critical terms.",
    ],
    "tool_routing": [
        "Review support tool selection logic in SupportTools.",
        "Add more emotion-to-tool mapping rules.",
        "Consider user preference history for tool selection.",
    ],
    "response_relevance": [
        "Improve emotion-to-response mapping in EmotionEngine.",
        "Add more diverse response templates for edge cases.",
        "Consider using Ollama LLM for higher-quality responses.",
    ],
    "fallback_reliability": [
        "Ensure EmotionEngine always returns a non-empty response.",
        "Add more fallback response templates for edge cases.",
        "Test with unusual inputs (special characters, very short/long text).",
    ],
    "voice_processing": [
        "Update pause thresholds for slow speakers in voice_config.yaml.",
        "Improve disfluency handling in transcript normalization.",
        "Add more Bangla voice test cases for better coverage.",
    ],
}


class ReportGenerator:
    """
    Generates accuracy evaluation reports.

    Usage:
        gen = ReportGenerator()
        print(gen.generate_console_report(results))
        gen.generate_json_report(results, "logs/accuracy_report.json")
    """

    def generate_console_report(self, results: Dict) -> str:
        """
        Generate a formatted console report string.

        Args:
            results: Output from AccuracyEvaluator.run_all()

        Returns:
            Formatted multi-line string for console output.
        """
        lines = []
        lines.append("")
        lines.append("=" * 60)
        lines.append("  ZARA ACCURACY EVALUATION REPORT")
        lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")

        # Overall accuracy
        overall = results.get("overall", 0.0)
        status = "PASS" if results.get("all_targets_met") else "FAIL"
        lines.append(f"  Overall Accuracy: {overall * 100:.1f}%  [{status}]")
        lines.append("")

        # Per-category results
        lines.append("  ── Per-Category Results ──────────────────────────")
        lines.append("")

        category_results = results.get("category_results", {})
        for cat, data in category_results.items():
            name = _CATEGORY_NAMES.get(cat, cat)
            acc = data.get("accuracy", 0.0)
            threshold = data.get("threshold", 0.90)
            passed = data.get("passed", False)
            indicator = "[PASS]" if passed else "[FAIL]"

            lines.append(
                f"  {indicator} {name:<25s} {acc * 100:5.1f}%  (target: {threshold * 100:.0f}%)"
            )

            # Show failure details if available
            cat_result = results.get(cat, {})
            failures = cat_result.get("failures", [])
            total = cat_result.get("total", 0)
            passed_count = cat_result.get("passed", 0)
            if failures:
                lines.append(f"    ({passed_count}/{total} passed, {len(failures)} failures)")

        lines.append("")

        # Recommendations
        recommendations = self.generate_recommendations(results)
        if recommendations:
            lines.append("  ── Recommendations ────────────────────────────────")
            lines.append("")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("")

        report = "\n".join(lines)
        return report

    def generate_json_report(self, results: Dict, path: Optional[str] = None):
        """
        Save evaluation results to a JSON file.

        Args:
            results: Output from AccuracyEvaluator.run_all()
            path: Output file path. Defaults to logs/accuracy_report.json.
        """
        if path is None:
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            path = str(log_dir / "accuracy_report.json")

        report = {
            "generated_at": datetime.now().isoformat(),
            "overall_accuracy": results.get("overall", 0.0),
            "all_targets_met": results.get("all_targets_met", False),
            "category_results": results.get("category_results", {}),
            "details": {},
            "recommendations": self.generate_recommendations(results),
        }

        # Include per-category details
        for cat in _CATEGORY_NAMES:
            if cat in results:
                report["details"][cat] = {
                    "accuracy": results[cat].get("accuracy", 0.0),
                    "total": results[cat].get("total", 0),
                    "passed": results[cat].get("passed", 0),
                    "failed": results[cat].get("failed", 0),
                    "failures": results[cat].get("failures", [])[:5],
                }

        try:
            output_path = Path(path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info("Accuracy report saved to %s", path)
        except OSError as e:
            logger.error("Failed to save accuracy report: %s", e)

    def generate_recommendations(self, results: Dict) -> List[str]:
        """
        Generate improvement recommendations based on failed categories.

        Args:
            results: Output from AccuracyEvaluator.run_all()

        Returns:
            List of recommendation strings.
        """
        recommendations = []
        category_results = results.get("category_results", {})

        for cat, data in category_results.items():
            if not data.get("passed", False):
                cat_recs = _RECOMMENDATIONS.get(cat, [])
                # Pick the top 2 recommendations for failed categories
                for rec in cat_recs[:2]:
                    recommendations.append(f"[{_CATEGORY_NAMES.get(cat, cat)}] {rec}")

        # If all targets met, add a positive note
        if results.get("all_targets_met"):
            recommendations.append(
                "All accuracy targets met! Continue monitoring for regressions."
            )

        return recommendations
