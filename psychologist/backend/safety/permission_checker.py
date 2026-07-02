"""
Permission Checker

Validates tool execution permissions based on risk level and safety policy.
No tool execution can happen without Safety Agent approval.
"""

import logging
from typing import Dict, Any, Optional

from .policy import SafetyPolicy, default_policy, RISK_HIGH

logger = logging.getLogger("zara.safety.permissions")


class PermissionChecker:
    """
    Checks whether a tool execution request is permitted.

    Evaluates:
      - Tool risk level against policy thresholds
      - Whether the action is in the blocked list
      - Whether user confirmation is required
    """

    def __init__(self, policy: Optional[SafetyPolicy] = None):
        self._policy = policy or default_policy

    def check_tool_permission(
        self,
        tool_name: str,
        risk_level: str = "low",
        action_name: str = "",
    ) -> Dict[str, Any]:
        """
        Check if a tool execution is permitted.

        Returns:
            Dict with:
              - permitted: True if execution is allowed
              - requires_confirmation: True if user must confirm
              - reason: explanation if blocked
              - risk_level: the evaluated risk level
        """
        # Check if the action is explicitly blocked
        check_name = action_name or tool_name
        if self._policy.is_action_blocked(check_name):
            logger.warning(
                "Tool blocked by policy: %s (action=%s)", tool_name, check_name
            )
            return {
                "permitted": False,
                "requires_confirmation": False,
                "reason": f"Action '{check_name}' is blocked by safety policy.",
                "risk_level": RISK_HIGH,
            }

        # Check if risk level blocks execution
        if self._policy.is_blocked(risk_level):
            logger.warning(
                "Tool blocked by risk level: %s (risk=%s)", tool_name, risk_level
            )
            return {
                "permitted": False,
                "requires_confirmation": False,
                "reason": (
                    f"Tool '{tool_name}' has risk level '{risk_level}' "
                    f"which exceeds the safety threshold."
                ),
                "risk_level": risk_level,
            }

        # Check if confirmation is required
        needs_confirmation = self._policy.requires_confirmation(risk_level)
        if needs_confirmation:
            logger.info(
                "Tool requires confirmation: %s (risk=%s)", tool_name, risk_level
            )

        return {
            "permitted": True,
            "requires_confirmation": needs_confirmation,
            "reason": "",
            "risk_level": risk_level,
        }

    def check_privacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if any data fields contain sensitive information.

        Returns:
            Dict with:
              - safe: True if no sensitive data found
              - flagged_fields: list of field names that may be sensitive
        """
        flagged = []
        for key in data:
            if key.lower() in self._policy.sensitive_fields:
                flagged.append(key)
            # Also check values for obvious patterns
            value = str(data.get(key, "")).lower()
            for sensitive in self._policy.sensitive_fields:
                if sensitive in value and len(value) < 200:
                    flagged.append(f"{key} (contains '{sensitive}')")
                    break

        return {
            "safe": len(flagged) == 0,
            "flagged_fields": flagged,
        }
