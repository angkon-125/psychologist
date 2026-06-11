from ..models import ConversationContext, EmotionalState
from ..sentiment_analysis import SentimentAnalyzer
from typing import List, Dict
import re


class ContextEngine:
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.context = ConversationContext()
        self.topic_keywords = {
            'work': ['work', 'job', 'career', 'office', 'boss', 'colleague', 'project', 'deadline'],
            'family': ['family', 'parent', 'mother', 'father', 'child', 'spouse', 'partner', 'relative'],
            'health': ['health', 'doctor', 'sick', 'ill', 'exercise', 'diet', 'medicine', 'hospital'],
            'relationships': ['relationship', 'friend', 'love', 'date', 'breakup', 'marriage', 'divorce'],
            'education': ['school', 'college', 'university', 'study', 'exam', 'teacher', 'student'],
            'finance': ['money', 'finance', 'budget', 'debt', 'bill', 'salary', 'income', 'expense'],
            'hobbies': ['hobby', 'game', 'sport', 'music', 'art', 'read', 'travel', 'vacation']
        }
        self.conversation_history: List[str] = []

    def update_context(self, text: str, emotional_state: EmotionalState) -> ConversationContext:
        self.conversation_history.append(text)
        if len(self.conversation_history) > 20:
            self.conversation_history.pop(0)
        
        sentiment_result = self.sentiment_analyzer.analyze_text(text)
        self.context.sentiment = sentiment_result['sentiment']
        
        self.context.emotional_trend.append(sentiment_result['sentiment'])
        self.context.intensity_trend.append(emotional_state.intensity)
        
        if len(self.context.emotional_trend) > 10:
            self.context.emotional_trend = self.context.emotional_trend[-10:]
        if len(self.context.intensity_trend) > 10:
            self.context.intensity_trend = self.context.intensity_trend[-10:]
        
        self.context.topic = self._detect_topic(text)
        self.context.current_topic_keywords = self._extract_topic_keywords(text)
        self.context.conflict_level = self._detect_conflict(text, emotional_state)
        self.context.motivation_opportunity = self._detect_motivation_opportunity(emotional_state)
        self.context.repeated_patterns = self._find_repeated_patterns()
        
        return self.context

    def _detect_topic(self, text: str) -> str:
        words = text.lower()
        topic_scores = {}
        
        for topic, keywords in self.topic_keywords.items():
            count = sum(1 for keyword in keywords if keyword in words)
            if count > 0:
                topic_scores[topic] = count
        
        if topic_scores:
            return max(topic_scores.items(), key=lambda x: x[1])[0]
        return 'general'

    def _extract_topic_keywords(self, text: str) -> List[str]:
        words = re.findall(r"\b\w+\b", text.lower())
        keywords = []
        for topic, topic_words in self.topic_keywords.items():
            for word in topic_words:
                if word in words:
                    keywords.append(word)
        return list(set(keywords))

    def _detect_conflict(self, text: str, emotional_state: EmotionalState) -> float:
        conflict = 0.0
        if emotional_state.primary_emotions['anger'] > 0.6:
            conflict += 0.4
        if emotional_state.primary_emotions['disgust'] > 0.5:
            conflict += 0.2
        if self.context.sentiment < -0.5:
            conflict += 0.3
        return min(1.0, conflict)

    def _detect_motivation_opportunity(self, emotional_state: EmotionalState) -> float:
        opportunity = 0.0
        if emotional_state.secondary_emotions['hope'] > 0.5:
            opportunity += 0.4
        if emotional_state.secondary_emotions['curiosity'] > 0.5:
            opportunity += 0.3
        if emotional_state.advanced_emotions['motivation'] > 0.4:
            opportunity += 0.3
        return min(1.0, opportunity)

    def _find_repeated_patterns(self) -> List[str]:
        patterns = []
        if len(self.conversation_history) < 3:
            return patterns
        
        word_freq = {}
        for text in self.conversation_history:
            words = re.findall(r"\b\w+\b", text.lower())
            for word in words:
                if len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        for word, count in word_freq.items():
            if count >= 3:
                patterns.append(word)
        
        return patterns

    def get_context_summary(self) -> Dict:
        return {
            'topic': self.context.topic,
            'sentiment': self.context.sentiment,
            'conflict_level': self.context.conflict_level,
            'motivation_opportunity': self.context.motivation_opportunity,
            'repeated_patterns': self.context.repeated_patterns,
            'topic_keywords': self.context.current_topic_keywords
        }
