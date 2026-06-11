from ..models import MemoryEntry, EmotionalState
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os


class EmotionalMemory:
    def __init__(self, max_short_term: int = 50, max_long_term: int = 1000):
        self.short_term_memory: List[MemoryEntry] = []
        self.long_term_memory: List[MemoryEntry] = []
        self.max_short_term = max_short_term
        self.max_long_term = max_long_term
        self.emotional_patterns: Dict[str, List[float]] = {}
        self.user_preferences: Dict = {}

    def add_memory(self, entry: MemoryEntry, is_important: bool = False):
        self.short_term_memory.append(entry)
        
        if len(self.short_term_memory) > self.max_short_term:
            self._transfer_to_long_term()
        
        if is_important or entry.importance > 0.7:
            self.long_term_memory.append(entry)
            if len(self.long_term_memory) > self.max_long_term:
                self.long_term_memory = sorted(self.long_term_memory, key=lambda x: x.importance, reverse=True)[:self.max_long_term]
        
        self._update_emotional_patterns(entry)

    def _transfer_to_long_term(self):
        if self.short_term_memory:
            oldest = self.short_term_memory.pop(0)
            if oldest.importance > 0.3:
                self.long_term_memory.append(oldest)
                if len(self.long_term_memory) > self.max_long_term:
                    self.long_term_memory.pop(0)

    def _update_emotional_patterns(self, entry: MemoryEntry):
        for emotion, value in {**entry.emotional_state.primary_emotions, **entry.emotional_state.secondary_emotions}.items():
            if emotion not in self.emotional_patterns:
                self.emotional_patterns[emotion] = []
            self.emotional_patterns[emotion].append(value)
            if len(self.emotional_patterns[emotion]) > 100:
                self.emotional_patterns[emotion] = self.emotional_patterns[emotion][-100:]

    def get_recent_memories(self, count: int = 10) -> List[MemoryEntry]:
        return self.short_term_memory[-count:]

    def get_memories_by_emotion(self, emotion: str, count: int = 10) -> List[MemoryEntry]:
        relevant = []
        for entry in self.long_term_memory + self.short_term_memory:
            all_emotions = {**entry.emotional_state.primary_emotions, **entry.emotional_state.secondary_emotions}
            if emotion in all_emotions and all_emotions[emotion] > 0.5:
                relevant.append(entry)
        return sorted(relevant, key=lambda x: x.timestamp, reverse=True)[:count]

    def get_emotional_trend(self, emotion: str, hours: int = 24) -> List[float]:
        cutoff = datetime.now() - timedelta(hours=hours)
        values = []
        for entry in self.short_term_memory:
            if entry.timestamp > cutoff:
                all_emotions = {**entry.emotional_state.primary_emotions, **entry.emotional_state.secondary_emotions}
                if emotion in all_emotions:
                    values.append(all_emotions[emotion])
        return values

    def get_average_emotion(self, emotion: str) -> float:
        if emotion in self.emotional_patterns and self.emotional_patterns[emotion]:
            return sum(self.emotional_patterns[emotion]) / len(self.emotional_patterns[emotion])
        return 0.0

    def update_preference(self, key: str, value: any):
        self.user_preferences[key] = value

    def get_preference(self, key: str, default: any = None) -> any:
        return self.user_preferences.get(key, default)

    def influence_current_emotion(self, current_state: EmotionalState) -> EmotionalState:
        for emotion in current_state.primary_emotions:
            avg = self.get_average_emotion(emotion)
            current_state.primary_emotions[emotion] = (
                current_state.primary_emotions[emotion] * 0.7 + avg * 0.3
            )
        return current_state

    def save_to_file(self, filepath: str):
        data = {
            'short_term': [m.to_dict() for m in self.short_term_memory],
            'long_term': [m.to_dict() for m in self.long_term_memory],
            'patterns': self.emotional_patterns,
            'preferences': self.user_preferences
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)

    def load_from_file(self, filepath: str):
        if not os.path.exists(filepath):
            return
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.emotional_patterns = data.get('patterns', {})
        self.user_preferences = data.get('preferences', {})
