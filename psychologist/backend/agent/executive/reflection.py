"""
Reflection Layer — Executive Brain

Post-response self-check that runs after response generation.
Checks for:
  - Misunderstood request (keyword overlap)
  - Ignored memory context
  - Forgot to use a needed tool
  - Contradicted earlier turns
  - Violated safety boundaries

Maximum one regeneration pass. No infinite loops.
Performance target: <50ms.
"""

import re
import logging
from typing import Optional

from .schemas import ExecutionPlan, ReflectionResult

logger = logging.getLogger("zara.executive.reflection")

# Safety boundary keywords that should never appear in responses
_SAFETY_VIOLATION_PATTERNS = [
    re.compile(r"\b(here'?s\s+how\s+to\s+(kill|end|hurt))\b", re.IGNORECASE),
    re.compile(r"\b(you\s+should\s+(die|end\s+it|self[- ]?harm))\b", re.IGNORECASE),
    re.compile(r"\b(diagnos(e|is|ed)|prescri(be|ption|ption)|medicat)\b", re.IGNORECASE),
    re.compile(r"\b(clinical\s+depression|bipolar|schizophrenia)\b.*\b(you\s+have|you'?re)\b", re.IGNORECASE),
]

# Contradiction indicators
_CONTRADICTION_PATTERNS = [
    re.compile(r"\b(i\s+(don'?t|didn'?t)\s+say)\b", re.IGNORECASE),
    re.compile(r"\b(that'?s\s+(not\s+)?(right|correct|true))\b.*\b(i\s+said)\b", re.IGNORECASE),
]


class ReflectionLayer:
    """
    Post-response self-check layer.

    Usage:
        reflection = ReflectionLayer()
        result = reflection.reflect(
            request_text="How do I open a file?",
            response_text="Here's how to open a file...",
            plan=plan,
            context="Previous: user asked about Python",
        )
    """

    def reflect(
        self,
        request_text: str,
        response_text: str,
        plan: Optional[ExecutionPlan] = None,
        context: str = "",
        intent: str = "",
    ) -> ReflectionResult:
        """
        Run post-response reflection checks.

        Args:
            request_text: What the user asked
            response_text: What ZARA responded
            plan: The execution plan that was followed
            context: Retrieved memory context
            intent: Classified intent

        Returns:
            ReflectionResult with issues found and whether to regenerate
        """
        issues = []
        issue_type = "none"

        # Check 1: Did response address the request?
        if not self._addresses_request(request_text, response_text, intent):
            issues.append("Response may not address the user's request")
            issue_type = "misunderstood"

        # Check 2: Was memory context available but ignored?
        if context and context.strip() and not self._uses_context(response_text, context):
            issues.append("Memory context was available but may not have been used")
            if issue_type == "none":
                issue_type = "ignored_memory"

        # Check 3: Were tools needed but not used?
        if plan and plan.required_tools:
            if not self._mentions_tools(response_text, plan.required_tools):
                issues.append("Tools were needed but may not have been invoked")
                if issue_type == "none":
                    issue_type = "forgot_tool"

        # Check 4: Does response contradict earlier turns?
        if context and context.strip():
            if self._contradicts_context(response_text, context):
                issues.append("Response may contradict earlier conversation")
                if issue_type == "none":
                    issue_type = "contradiction"

        # Check 5: Does response violate safety boundaries?
        if self._violates_safety(response_text):
            issues.append("Response may violate safety boundaries")
            issue_type = "safety_violation"  # Always overrides

        # Determine if regeneration is needed
        should_regenerate = len(issues) > 0 and issue_type in (
            "misunderstood", "safety_violation"
        )

        result = ReflectionResult(
            issues_found=issues,
            should_regenerate=should_regenerate,
            issue_type=issue_type,
        )

        if issues:
            logger.info(
                "Reflection: %d issues found (type=%s, regenerate=%s)",
                len(issues), issue_type, should_regenerate,
            )
        else:
            logger.debug("Reflection: no issues found")

        return result

    def _addresses_request(self, request: str, response: str, intent: str) -> bool:
        """Check if response addresses the request (keyword overlap)."""
        if not request or not response:
            return True  # Can't check, assume ok

        # For greetings/farewells, any response addresses the request
        if intent in ("greeting", "farewell"):
            return True

        # Extract meaningful words from request (3+ chars)
        request_words = set(
            w.lower() for w in re.findall(r'\b\w{3,}\b', request)
        ) - {"the", "and", "for", "that", "this", "with", "have", "from",
             "are", "was", "were", "been", "can", "could", "would", "should"}

        if not request_words:
            return True  # No meaningful words to check

        response_lower = response.lower()
        # At least one meaningful word from request should appear in response
        overlap = sum(1 for w in request_words if w in response_lower)
        return overlap >= 1 or len(request_words) <= 2

    def _uses_context(self, response: str, context: str) -> bool:
        """Check if response uses any information from context."""
        if not context or not response:
            return True

        # Extract key terms from context
        context_words = set(
            w.lower() for w in re.findall(r'\b\w{4,}\b', context)
        ) - {"user", "zara", "that", "this", "with", "have", "from"}

        if not context_words:
            return True

        response_lower = response.lower()
        overlap = sum(1 for w in context_words if w in response_lower)
        # Having at least 1 overlap suggests context was used
        return overlap >= 1

    def _mentions_tools(self, response: str, required_tools: list) -> bool:
        """Check if response mentions tool-related actions."""
        if not response:
            return False
        response_lower = response.lower()
        tool_keywords = ["file", "command", "scan", "list", "create", "delete",
                         "open", "execute", "run", "system", "disk", "operation"]
        return any(kw in response_lower for kw in tool_keywords)

    def _contradicts_context(self, response: str, context: str) -> bool:
        """Check if response contradicts earlier conversation turns."""
        if not response or not context:
            return False
        return any(p.search(response) for p in _CONTRADICTION_PATTERNS)

    def _violates_safety(self, response: str) -> bool:
        """Check if response violates safety boundaries."""
        if not response:
            return False
        return any(p.search(response) for p in _SAFETY_VIOLATION_PATTERNS)
