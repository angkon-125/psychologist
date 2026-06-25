"""
Support Tools

Pre-written supportive content for calming exercises, breathing,
journaling prompts, reflection questions, mood check-ins, and
grounding exercises.

All content is pre-authored — no LLM, no generation.
Available in English and Bangla.
"""

import random
from typing import Dict, List, Optional
from datetime import datetime

from .interaction_models import SupportAction


class SupportTools:
    """Provides safe, pre-written supportive content."""

    def __init__(self):
        self._scripts = self._init_scripts()

    # ── Public API ───────────────────────────────────────────────

    def calm_down(self, language: str = "en") -> SupportAction:
        """Get a calming exercise."""
        return self._build_action(
            "calm_down", "User requested calming support", language
        )

    def breathing_exercise(self, language: str = "en") -> SupportAction:
        """Get a guided breathing exercise."""
        return self._build_action(
            "breathing_exercise", "User requested breathing exercise", language
        )

    def journaling_prompt(
        self, language: str = "en", emotion: Optional[str] = None
    ) -> SupportAction:
        """Get a journaling prompt, optionally tailored to current emotion."""
        action = self._build_action(
            "journaling_prompt", "User requested journaling prompt", language
        )
        # Add emotion-specific prefix if available
        if emotion and language == "en":
            action.content = (
                f"You mentioned feeling {emotion}. "
                + action.content
            )
        elif emotion and language in ("bn", "bn_bd"):
            action.content = (
                f"তুমি {emotion} অনুভব করছো। "
                + action.content
            )
        return action

    def reflection_questions(self, language: str = "en") -> SupportAction:
        """Get self-reflection questions."""
        return self._build_action(
            "reflection_questions", "User requested reflection questions", language
        )

    def mood_checkin(self, language: str = "en") -> SupportAction:
        """Get a mood check-in prompt."""
        return self._build_action(
            "mood_checkin", "User requested mood check-in", language
        )

    def grounding_exercise(self, language: str = "en") -> SupportAction:
        """Get a grounding exercise (5-4-3-2-1 technique)."""
        return self._build_action(
            "grounding_exercise", "User requested grounding exercise", language
        )

    def session_summary_prompt(self, language: str = "en") -> SupportAction:
        """Get a closing summary prompt."""
        return self._build_action(
            "session_summary", "End of session summary", language
        )

    # ── Action builder ───────────────────────────────────────────

    def _build_action(
        self, action_type: str, reason: str, language: str
    ) -> SupportAction:
        lang_key = "bn" if language in ("bn", "bn_bd") else "en"
        scripts = self._scripts.get(action_type, {}).get(lang_key, [])
        content = random.choice(scripts) if scripts else ""
        return SupportAction(
            action_type=action_type,
            trigger_reason=reason,
            script_key=f"{action_type}_{lang_key}",
            language=lang_key,
            completed=False,
            content=content,
        )

    # ── Script library ───────────────────────────────────────────

    @staticmethod
    def _init_scripts() -> Dict[str, Dict[str, List[str]]]:
        return {
            "calm_down": {
                "en": [
                    "Let's slow things down. Close your eyes gently if you can. Take a slow breath in through your nose... hold it for a moment... and let it out slowly through your mouth. You're safe right now. There's no rush.",
                    "I'm here with you. Let's pause together. Place your hands on your lap and feel the weight of them resting there. Take three slow breaths. With each exhale, let your shoulders drop a little lower.",
                    "Everything can wait for a moment. Right now, it's just you and this moment. Try unclenching your jaw and relaxing your hands. Take a deep breath and let it go gently.",
                ],
                "bn": [
                    "চলো একটু ধীরে যাই। চোখ বন্ধ করো যদি পারো। নাক দিয়ে ধীরে ধীরে শ্বাস নাও... একটু ধরে রাখো... এবার মুখ দিয়ে আস্তে আস্তে ছাড়ো। তুমি এখন নিরাপদ।",
                    "আমি তোমার পাশে আছি। চলো একসাথে থামি। তোমার হাত দুটো কোলে রাখো এবং তাদের ওজন অনুভব করো। তিনটে ধীর শ্বাস নাও। প্রতিটা শ্বাসে কাঁধ একটু নামাও।",
                ],
            },
            "breathing_exercise": {
                "en": [
                    "Let's try the 4-7-8 breathing technique:\n\n1. Breathe in through your nose for 4 seconds\n2. Hold your breath for 7 seconds\n3. Exhale slowly through your mouth for 8 seconds\n\nLet's do this together 3 times. Ready? Breathe in... hold... and breathe out...",
                    "Let's try box breathing:\n\n1. Breathe in for 4 counts\n2. Hold for 4 counts\n3. Breathe out for 4 counts\n4. Hold for 4 counts\n\nRepeat this cycle 4 times. I'll count with you. Breathe in... 1, 2, 3, 4...",
                    "Simple deep breathing: Place one hand on your chest and one on your belly. Breathe in slowly until you feel your belly rise. Hold for a moment. Then let it out slowly. Your belly should lower as you exhale. Try this 5 times at your own pace.",
                ],
                "bn": [
                    "চলো ৪-৭-৮ শ্বাস-প্রশ্বাস পদ্ধতি চেষ্টা করি:\n\n১. নাক দিয়ে ৪ সেকেন্ড শ্বাস নাও\n২. ৭ সেকেন্ড ধরে রাখো\n৩. মুখ দিয়ে ৮ সেকেন্ড ধরে আস্তে আস্তে শ্বাস ছাড়ো\n\nচলো একসাথে ৩ বার করি। শুরু করো... শ্বাস নাও... ধরো... এবং ছাড়ো...",
                    "বক্স ব্রিদিং চেষ্টা করি:\n\n১. ৪ গণনায় শ্বাস নাও\n২. ৪ গণনায় ধরে রাখো\n৩. ৪ গণনায় শ্বাস ছাড়ো\n৪. ৪ গণনায় ধরে রাখো\n\nএই চক্রটি ৪ বার পুনরাবৃত্তি করো।",
                ],
            },
            "journaling_prompt": {
                "en": [
                    "Try writing about this: What are three things you felt today, and what might have caused each one?",
                    "Here's a journaling idea: Write a letter to yourself as if you were comforting a close friend going through the same thing.",
                    "Journaling prompt: What is weighing on you the most right now? Write it down without judging yourself. Just let the words flow.",
                    "Try finishing this sentence in writing: 'Right now I feel _____ because _____.' Then ask yourself: 'What do I need most right now?'",
                    "Write down one thing that went well today, no matter how small. Then write one thing you wish had gone differently. What can you learn from both?",
                ],
                "bn": [
                    "এটা লিখে দেখো: আজ তুমি তিনটি কী অনুভব করেছো এবং প্রতিটির কারণ কী হতে পারে?",
                    "একটা জার্নালিং আইডিয়া: নিজেকে একটা চিঠি লেখো যেন তুমি একজন কাছের বন্ধুকে সান্ত্বনা দিচ্ছো যে একই পরিস্থিতিতে আছে।",
                    "এই বাক্যটি সম্পূর্ণ করো: 'এখন আমি _____ অনুভব করছি কারণ _____।' তারপর নিজেকে জিজ্ঞেস করো: 'আমার এখন সবচেয়ে বেশি কী দরকার?'",
                ],
            },
            "reflection_questions": {
                "en": [
                    "Here are some questions to reflect on:\n\n• What emotion am I feeling most strongly right now?\n• When did this feeling start?\n• Is there something I can do right now to take care of myself?\n• What would I tell a friend who felt this way?",
                    "Some gentle reflection:\n\n• What has been taking up most of my mental energy lately?\n• Am I being kind to myself about this?\n• What is one small thing I can do today that would make tomorrow a little easier?",
                    "Questions for self-understanding:\n\n• What am I grateful for today, even if it's small?\n• What boundaries do I need to set or protect?\n• What does my best self look like when handling this?",
                ],
                "bn": [
                    "কিছু প্রশ্ন নিজেকে জিজ্ঞেস করো:\n\n• এখন আমি সবচেয়ে জোরালোভাবে কী অনুভব করছি?\n• এই অনুভূতি কখন শুরু হয়েছিল?\n• এখনই নিজের যত্ন নেওয়ার জন্য আমি কী করতে পারি?\n• আমার বন্ধু এমন অনুভব করলে আমি তাকে কী বলতাম?",
                    "মৃদু আত্মচিন্তন:\n\n• সম্প্রতি কোন জিনিস আমার মানসিক শক্তি সবচেয়ে বেশি নিচ্ছে?\n• আমি কি এ বিষয়ে নিজের প্রতি সদয় হচ্ছি?\n• আজ একটি ছোট জিনিস কী করতে পারি যা আগামীকাল একটু সহজ করবে?",
                ],
            },
            "mood_checkin": {
                "en": [
                    "Let's check in with how you're feeling.\n\nOn a scale from 1 to 5:\n1 — Very low / struggling\n2 — Low / not great\n3 — Okay / neutral\n4 — Good / positive\n5 — Great / energised\n\nHow would you rate your mood right now? There's no wrong answer.",
                    "Mood check-in time.\n\nTake a moment to notice what's happening inside:\n• How is your body feeling? (tense, relaxed, tired?)\n• What emotion stands out most?\n• Is there something on your mind you haven't said yet?\n\nShare whatever feels right.",
                ],
                "bn": [
                    "চলো দেখি তুমি কেমন অনুভব করছো।\n\n১ থেকে ৫ এর স্কেলে:\n১ — খুব খারাপ\n২ — খারাপ\n৩ — ঠিকঠাক\n৪ — ভালো\n৫ — খুব ভালো\n\nএখন তোমার মেজাজ কত? কোনো ভুল উত্তর নেই।",
                ],
            },
            "grounding_exercise": {
                "en": [
                    "Let's try the 5-4-3-2-1 grounding exercise:\n\n🔵 Name 5 things you can SEE\n🟢 Name 4 things you can TOUCH\n🟡 Name 3 things you can HEAR\n🟠 Name 2 things you can SMELL\n🔴 Name 1 thing you can TASTE\n\nTake your time with each one. This helps bring you back to the present moment.",
                    "Grounding technique: Press your feet firmly into the floor. Feel the ground beneath you. Wiggle your toes. Notice the texture of what you're sitting on. Run your fingers along a surface near you. You are here. You are present. You are safe.",
                ],
                "bn": [
                    "৫-৪-৩-২-১ গ্রাউন্ডিং এক্সারসাইজ:\n\n🔵 ৫টি জিনিস বলো যা তুমি দেখতে পাচ্ছো\n🟢 ৪টি জিনিস বলো যা তুমি স্পর্শ করতে পারো\n🟡 ৩টি জিনিস বলো যা তুমি শুনতে পাচ্ছো\n🟠 ২টি জিনিস বলো যার গন্ধ পাচ্ছো\n🔴 ১টি জিনিস বলো যার স্বাদ পাচ্ছো\n\nপ্রতিটিতে সময় নাও। এটি তোমাকে বর্তমান মুহূর্তে ফিরিয়ে আনতে সাহায্য করবে।",
                ],
            },
            "session_summary": {
                "en": [
                    "As we wrap up this session, take a moment to reflect:\n\n• What was the most helpful part of our conversation?\n• How are you feeling now compared to when we started?\n• Is there anything you'd like to carry forward from today?\n\nRemember, every conversation is a step forward. You're doing great.",
                ],
                "bn": [
                    "এই সেশন শেষ করার আগে একটু ভাবো:\n\n• আমাদের কথোপকথনের সবচেয়ে সহায়ক অংশ কী ছিল?\n• শুরুর তুলনায় এখন তুমি কেমন অনুভব করছো?\n• আজকের থেকে কিছু কি তুমি সামনে নিয়ে যেতে চাও?\n\nমনে রেখো, প্রতিটি কথোপকথন একটি পদক্ষেপ এগিয়ে। তুমি ভালো করছো।",
                ],
            },
        }
