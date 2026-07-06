"""
Intent Router

Classifies user input into intents using keyword matching and pattern rules.
No ML dependency — fully offline, deterministic, and fast.

Intents map directly to specialist agents:
  - emotional_support → Psychologist Agent
  - crisis           → Safety Agent (immediate)
  - tool_request      → Tool Agent
  - voice_command     → Voice Agent
  - journaling        → Psychologist Agent
  - breathing         → Psychologist Agent
  - reflection        → Psychologist Agent
  - mood_checkin      → Psychologist Agent
  - greeting          → LLM Agent
  - farewell          → LLM Agent
  - prediction        → Prediction Agent
  - general           → LLM Agent (default)
"""

import re
import logging
from typing import Dict, Tuple

logger = logging.getLogger("zara.agent.router")

# ── Intent definitions ────────────────────────────────────────────

INTENT_CRISIS = "crisis"
INTENT_EMOTIONAL_SUPPORT = "emotional_support"
INTENT_JOURNALING = "journaling"
INTENT_BREATHING = "breathing"
INTENT_REFLECTION = "reflection"
INTENT_MOOD_CHECKIN = "mood_checkin"
INTENT_GROUNDING = "grounding"
INTENT_TOOL_REQUEST = "tool_request"
INTENT_VOICE_COMMAND = "voice_command"
INTENT_GREETING = "greeting"
INTENT_FAREWELL = "farewell"
INTENT_PREDICTION = "prediction"
INTENT_SESSION_SUMMARY = "session_summary"
INTENT_GENERAL = "general"

# ── Agent mapping ─────────────────────────────────────────────────

INTENT_TO_AGENT = {
    INTENT_CRISIS: "safety",
    INTENT_EMOTIONAL_SUPPORT: "psychologist",
    INTENT_JOURNALING: "psychologist",
    INTENT_BREATHING: "psychologist",
    INTENT_REFLECTION: "psychologist",
    INTENT_MOOD_CHECKIN: "psychologist",
    INTENT_GROUNDING: "psychologist",
    INTENT_TOOL_REQUEST: "tool",
    INTENT_VOICE_COMMAND: "voice",
    INTENT_GREETING: "llm",
    INTENT_FAREWELL: "llm",
    INTENT_PREDICTION: "prediction",
    INTENT_SESSION_SUMMARY: "psychologist",
    INTENT_GENERAL: "llm",
}

# ── Keyword patterns (English + Bangla) ───────────────────────────

_CRISIS_KEYWORDS = [
    r"\bsuicid", r"\bkill\s+(my|him|her|them)?self",
    r"\bwant\s+to\s+die\b", r"\bend\s+(my|it|this)\s+life\b",
    r"\bself[- ]?harm\b", r"\bcut\s+(my)?self\b",
    r"\boverdose\b", r"\bjump\s+off\b",
    r"\bআত্মহত্যা\b", r"\bমরে\s+যেতে\b", r"\bনিজেকে\s+শেষ\b",
]

_EMOTIONAL_SUPPORT_KEYWORDS = [
    r"\bsad\b", r"\bdepressed\b", r"\blonely\b", r"\banxious\b",
    r"\bstressed\b", r"\boverwhelmed\b", r"\bhurt(ing)?\b",
    r"\bscared\b", r"\bafraid\b", r"\bcrying\b", r"\bworried\b",
    r"\bmiserable\b", r"\bhopeless\b", r"\bhelpless\b",
    r"\bbroken\b", r"\bstruggling\b", r"\bsuffering\b",
    r"\bi feel\b", r"\bi'm feeling\b", r"\bfeeling\s+(so|really|very)\b",
    r"\bupset\b", r"\bfrustrated\b", r"\bangry\b", r"\bexhausted\b",
    r"\bকষ্ট\b", r"\bদুঃখিত\b", r"\bএকা\b", r"\bভয়\b",
    r"\bচিন্তিত\b", r"\bউদ্বিগ্ন\b", r"\bহতাশ\b",
]

_JOURNALING_KEYWORDS = [
    r"\bjournal\b", r"\bdiary\b", r"\bwrite\s+(about|down)\b",
    r"\blog\s+my\b", r"\bjournaling\b",
    r"\bডায়েরি\b", r"\bলিখতে\b",
]

_BREATHING_KEYWORDS = [
    r"\bbreath(e|ing)\b", r"\bcalm\s+(me|down)\b",
    r"\brelax\b", r"\bbreathwork\b",
    r"\bশ্বাস\b", r"\bশান্ত\b",
]

_REFLECTION_KEYWORDS = [
    r"\breflect(ion)?\b", r"\bthink\s+about\b",
    r"\bself[- ]?reflect\b", r"\bintrospect\b",
]

_MOOD_CHECKIN_KEYWORDS = [
    r"\bmood\s*check\b", r"\bhow\s+am\s+i\b", r"\bcheck\s*in\b",
    r"\bmood\b.*\btoday\b",
]

_GROUNDING_KEYWORDS = [
    r"\bground(ing|ed)?\b", r"\b5[- ]?4[- ]?3[- ]?2[- ]?1\b",
    r"\bpanic\b", r"\banxiety\s+attack\b",
]

_TOOL_KEYWORDS = [
    r"\bopen\s+file\b", r"\blist\s+files\b", r"\bscan\s+project\b",
    r"\brun\s+command\b", r"\bexecute\b", r"\blaunch\b",
    r"\bsystem\s+info\b", r"\bdisk\s+usage\b", r"\bcpu\b",
    r"\bmemory\s+usage\b", r"\bdisk\b",
    r"\bfile\b.*\b(read|write|create|delete)\b",
]

_VOICE_COMMAND_KEYWORDS = [
    r"\bstop\s+(listening|speaking|talking)\b",
    r"\bstart\s+listening\b", r"\bvoice\s+mode\b",
    r"\bmute\b", r"\bunmute\b", r"\bspeak\b",
]

_GREETING_KEYWORDS = [
    r"\b(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))\b",
    r"\bhow\s+are\s+you\b", r"\bwhat's\s+up\b",
    r"\bহ্যালো\b", r"\bনমস্কার\b", r"\bকেমন\s+আছ\b",
]

_FAREWELL_KEYWORDS = [
    r"\b(bye|goodbye|good\s*night|see\s+you|take\s+care)\b",
    r"\bend\s+session\b", r"\bthat's\s+all\b",
    r"\bবিদায়\b", r"\bশুভরাত্রি\b",
]

_PREDICTION_KEYWORDS = [
    r"\bpredict\b", r"\bforecast\b", r"\bwhat\s+will\b",
    r"\bwhat\s+might\b", r"\brisk\b.*\bassess\b",
    r"\bnext\s+step\b", r"\brecommend(ation)?\b",
]

_SESSION_SUMMARY_KEYWORDS = [
    r"\bsummar(y|ize|ise)\b", r"\bwrap\s+up\b",
    r"\bsession\s+summary\b", r"\breview\s+session\b",
]


class IntentRouter:
    """
    Classifies user text into intents and maps to target agents.

    Usage:
        router = IntentRouter()
        intent, confidence, agent = router.classify("I feel so sad today")
        # → ("emotional_support", 0.85, "psychologist")
    """

    def __init__(self):
        # Compile patterns once for performance
        self._patterns = {
            INTENT_CRISIS: [re.compile(p, re.IGNORECASE) for p in _CRISIS_KEYWORDS],
            INTENT_EMOTIONAL_SUPPORT: [
                re.compile(p, re.IGNORECASE) for p in _EMOTIONAL_SUPPORT_KEYWORDS
            ],
            INTENT_JOURNALING: [
                re.compile(p, re.IGNORECASE) for p in _JOURNALING_KEYWORDS
            ],
            INTENT_BREATHING: [
                re.compile(p, re.IGNORECASE) for p in _BREATHING_KEYWORDS
            ],
            INTENT_REFLECTION: [
                re.compile(p, re.IGNORECASE) for p in _REFLECTION_KEYWORDS
            ],
            INTENT_MOOD_CHECKIN: [
                re.compile(p, re.IGNORECASE) for p in _MOOD_CHECKIN_KEYWORDS
            ],
            INTENT_GROUNDING: [
                re.compile(p, re.IGNORECASE) for p in _GROUNDING_KEYWORDS
            ],
            INTENT_TOOL_REQUEST: [
                re.compile(p, re.IGNORECASE) for p in _TOOL_KEYWORDS
            ],
            INTENT_VOICE_COMMAND: [
                re.compile(p, re.IGNORECASE) for p in _VOICE_COMMAND_KEYWORDS
            ],
            INTENT_GREETING: [
                re.compile(p, re.IGNORECASE) for p in _GREETING_KEYWORDS
            ],
            INTENT_FAREWELL: [
                re.compile(p, re.IGNORECASE) for p in _FAREWELL_KEYWORDS
            ],
            INTENT_PREDICTION: [
                re.compile(p, re.IGNORECASE) for p in _PREDICTION_KEYWORDS
            ],
            INTENT_SESSION_SUMMARY: [
                re.compile(p, re.IGNORECASE) for p in _SESSION_SUMMARY_KEYWORDS
            ],
        }

        # Priority order: crisis first, then more specific intents
        self._priority = [
            INTENT_CRISIS,
            INTENT_TOOL_REQUEST,
            INTENT_VOICE_COMMAND,
            INTENT_JOURNALING,
            INTENT_BREATHING,
            INTENT_GROUNDING,
            INTENT_REFLECTION,
            INTENT_MOOD_CHECKIN,
            INTENT_SESSION_SUMMARY,
            INTENT_PREDICTION,
            INTENT_EMOTIONAL_SUPPORT,
            INTENT_FAREWELL,
            INTENT_GREETING,
        ]

    def classify(self, text: str) -> Tuple[str, float, str]:
        """
        Classify user text into an intent.

        Returns:
            (intent, confidence, target_agent)
        """
        if not text or not text.strip():
            return INTENT_GENERAL, 0.0, INTENT_TO_AGENT[INTENT_GENERAL]

        text_lower = text.lower().strip()

        # Check intents in priority order
        for intent in self._priority:
            patterns = self._patterns.get(intent, [])
            match_count = sum(1 for p in patterns if p.search(text_lower))
            if match_count > 0:
                # Confidence based on match density
                confidence = min(0.95, 0.6 + (match_count * 0.1))
                # Crisis is always high confidence
                if intent == INTENT_CRISIS:
                    confidence = max(confidence, 0.90)
                agent = INTENT_TO_AGENT[intent]
                logger.info(
                    "Intent: %s (confidence=%.2f, agent=%s, matches=%d)",
                    intent, confidence, agent, match_count,
                )
                return intent, confidence, agent

        # Default: general conversation → LLM
        logger.info("Intent: general (default, no pattern matched)")
        return INTENT_GENERAL, 0.5, INTENT_TO_AGENT[INTENT_GENERAL]

    def get_agent_for_intent(self, intent: str) -> str:
        """Get the target agent name for a given intent."""
        return INTENT_TO_AGENT.get(intent, INTENT_TO_AGENT[INTENT_GENERAL])
