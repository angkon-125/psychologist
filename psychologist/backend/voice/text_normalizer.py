"""
ZARA Text Normalizer and Sentence Chunker

Prepares text for natural-sounding speech synthesis:
  - Strips markdown formatting (bold, italic, headings, links)
  - Removes code fences and JSON blocks
  - Converts bullet lists to natural speech
  - Shortens overly long sentences
  - Replaces URLs with "[link]"
  - Adds pause markers after emotional sentences
  - Preserves Bangla (and other Unicode) text intact

Also provides sentence chunking for long responses:
  - Splits on sentence boundaries
  - Respects max_sentence_chars from speaking style
  - Avoids cutting mid-word or mid-number

No voice cloning. No celebrity imitation. No cloud voice.
"""

import re
import logging
from typing import List, Optional

logger = logging.getLogger("zara.voice.normalizer")

# ── Regex Patterns ─────────────────────────────────────────────────────────

# Code fences: ```...``` (multiline)
_RE_CODE_FENCE = re.compile(r"```[\s\S]*?```", re.MULTILINE)

# Inline code: `code`
_RE_INLINE_CODE = re.compile(r"`([^`]+)`")

# Markdown bold: **text** or __text__
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")

# Markdown italic: *text* or _text_ (but not inside bold)
_RE_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|(?<!_)_(?!_)(.+?)(?<!_)_(?!_)")

# Headings: # text, ## text, etc.
_RE_HEADING = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)

# Markdown links: [text](url)
_RE_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")

# Bare URLs (http/https)
_RE_URL = re.compile(r"https?://[^\s\)>\]]+")

# Bullet lists: - item, * item, 1. item
_RE_BULLET = re.compile(r"^[\s]*[-*]\s+(.+)$", re.MULTILINE)
_RE_NUMBERED = re.compile(r"^[\s]*\d+[.)]\s+(.+)$", re.MULTILINE)

# Sentence terminators
_RE_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

# Emotional phrases that should get a pause after them
_EMOTIONAL_PHRASES = [
    "i understand",
    "i'm sorry",
    "i am sorry",
    "it's okay",
    "it is okay",
    "that's alright",
    "that is alright",
    "i'm here",
    "i am here",
    "take your time",
    "you're safe",
    "you are safe",
    "i hear you",
    "that must be",
    "i can see that",
    "it's normal",
    "it is normal",
    "don't worry",
    "do not worry",
]

# JSON block detection
_RE_JSON_BLOCK = re.compile(r"^\s*\{[\s\S]*\}\s*$")


def normalize_for_speech(text: str, language: str = "en") -> str:
    """
    Normalize text for natural-sounding speech synthesis.

    Steps:
      1. Remove code fences and inline code
      2. Remove JSON blocks
      3. Strip markdown formatting
      4. Convert bullet/numbered lists to natural speech
      5. Replace URLs with "[link]"
      6. Shorten very long sentences
      7. Add pause markers after emotional phrases
      8. Clean up whitespace

    Preserves Bangla and other Unicode text.
    """
    if not text or not text.strip():
        return ""

    result = text

    # 1. Remove code fences
    result = _RE_CODE_FENCE.sub(" ", result)

    # 2. Remove inline code (keep content)
    result = _RE_INLINE_CODE.sub(r"\1", result)

    # 3. Skip JSON blocks entirely
    if _RE_JSON_BLOCK.match(result.strip()):
        logger.debug("Skipping JSON block for speech")
        return ""

    # 4. Convert links: [text](url) -> text
    result = _RE_LINK.sub(r"\1", result)

    # 5. Replace bare URLs with [link]
    result = _RE_URL.sub("[link]", result)

    # 6. Strip headings: ## Title -> Title
    result = _RE_HEADING.sub(r"\1", result)

    # 7. Strip bold/italic markers
    result = _RE_BOLD.sub(r"\1\2", result)
    result = _RE_ITALIC.sub(r"\1\2", result)

    # 8. Convert bullet lists to "item. item."
    result = _RE_BULLET.sub(r"\1.", result)
    result = _RE_NUMBERED.sub(r"\1.", result)

    # 9. Add pause markers after emotional phrases
    result = _add_emotional_pauses(result)

    # 10. Clean up whitespace
    result = re.sub(r"[ \t]+", " ", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = re.sub(r"\n+", " ", result)
    result = result.strip()

    # 11. Collapse multiple spaces
    result = re.sub(r" {2,}", " ", result)

    return result


def _add_emotional_pauses(text: str) -> str:
    """Add pause markers (...) after emotional phrases."""
    result = text
    lower = result.lower()

    for phrase in _EMOTIONAL_PHRASES:
        # Find phrase followed by sentence continuation (not already paused)
        idx = 0
        while True:
            pos = lower.find(phrase, idx)
            if pos == -1:
                break
            end_pos = pos + len(phrase)
            # Check if there's already a pause or sentence end right after
            remaining = result[end_pos:end_pos + 5].strip()
            if remaining and not remaining.startswith("...") and not remaining.startswith(".") and not remaining.startswith("!") and not remaining.startswith("?"):
                # Insert pause after the phrase
                result = result[:end_pos] + "..." + result[end_pos:]
                lower = result.lower()
                idx = end_pos + 3
            else:
                idx = end_pos

    return result


def chunk_for_speech(
    text: str,
    max_chars: int = 150,
    chunk_mode: str = "sentence",
) -> List[str]:
    """
    Split text into spoken chunks suitable for TTS playback.

    Args:
        text: Normalized text to chunk
        max_chars: Maximum characters per chunk
        chunk_mode: "sentence" (split on sentences) or "short" (aggressive splitting)

    Returns:
        List of chunk strings, each <= max_chars where possible.
        Empty chunks are filtered out.
    """
    if not text or not text.strip():
        return []

    # Split into sentences
    sentences = _RE_SENTENCE_END.split(text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [text.strip()] if text.strip() else []

    chunks = []

    if chunk_mode == "short":
        # Aggressive: each sentence is its own chunk, split further if too long
        for sentence in sentences:
            if len(sentence) <= max_chars:
                chunks.append(sentence)
            else:
                # Split on commas, semicolons, colons
                sub_parts = re.split(r"[,;:]\s+", sentence)
                current = ""
                for part in sub_parts:
                    if current and len(current) + len(part) + 2 > max_chars:
                        chunks.append(current.strip())
                        current = part
                    else:
                        current = current + ", " + part if current else part
                if current.strip():
                    chunks.append(current.strip())
    else:
        # Sentence mode: group sentences up to max_chars
        current = ""
        for sentence in sentences:
            if not current:
                current = sentence
            elif len(current) + len(sentence) + 1 <= max_chars:
                current = current + " " + sentence
            else:
                # If current sentence is already too long, split it
                if len(current) > max_chars:
                    sub_parts = re.split(r"[,;:]\s+", current)
                    sub_current = ""
                    for part in sub_parts:
                        if sub_current and len(sub_current) + len(part) + 2 > max_chars:
                            chunks.append(sub_current.strip())
                            sub_current = part
                        else:
                            sub_current = sub_current + ", " + part if sub_current else part
                    if sub_current.strip():
                        chunks.append(sub_current.strip())
                else:
                    chunks.append(current)
                current = sentence

        if current.strip():
            # Check if last chunk is too long
            if len(current) > max_chars:
                sub_parts = re.split(r"[,;:]\s+", current)
                sub_current = ""
                for part in sub_parts:
                    if sub_current and len(sub_current) + len(part) + 2 > max_chars:
                        chunks.append(sub_current.strip())
                        sub_current = part
                    else:
                        sub_current = sub_current + ", " + part if sub_current else part
                if sub_current.strip():
                    chunks.append(sub_current.strip())
            else:
                chunks.append(current)

    # Filter empty chunks
    chunks = [c.strip() for c in chunks if c.strip()]

    return chunks
