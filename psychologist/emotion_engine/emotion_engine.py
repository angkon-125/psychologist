from .models import EmotionalState, PersonalityTraits, MemoryEntry, ConversationContext
from .personality_engine import PersonalityEngine
from .emotional_memory import EmotionalMemory
from .sentiment_analysis import SentimentAnalyzer
from .context_engine import ContextEngine
from .reasoning_engine import ReasoningEngine
from .behavior_predictor import BehaviorPredictor
from .response_generator import ResponseGenerator
from typing import Dict, List, Optional


class EmotionEngine:
    def __init__(self, personality_traits: Optional[PersonalityTraits] = None):
        self.personality_engine = PersonalityEngine(personality_traits)
        self.emotional_memory = EmotionalMemory()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.context_engine = ContextEngine()
        self.reasoning_engine = ReasoningEngine()
        self.behavior_predictor = BehaviorPredictor()
        self.response_generator = ResponseGenerator()
        
        self.current_emotional_state = EmotionalState()
        self.emotional_history: List[EmotionalState] = []
        self.interaction_count = 0

    def process_input(self, text: str, additional_emotions: Optional[Dict] = None) -> Dict:
        self.interaction_count += 1
        
        sentiment_result = self.sentiment_analyzer.analyze_text(text)
        emotion_keywords = self.sentiment_analyzer.detect_emotion_keywords(text)
        
        self._update_emotional_state(sentiment_result, emotion_keywords, additional_emotions)
        
        context = self.context_engine.update_context(text, self.current_emotional_state)
        
        reasoning_result = self.reasoning_engine.reason(
            self.current_emotional_state,
            context,
            self.personality_engine.traits
        )
        
        self._apply_reasoning_to_emotions(reasoning_result)
        
        self.emotional_history.append(self.current_emotional_state)
        if len(self.emotional_history) > 100:
            self.emotional_history = self.emotional_history[-100:]
        
        memory_entry = MemoryEntry(
            interaction=text,
            emotional_state=self.current_emotional_state,
            context=self.context_engine.get_context_summary(),
            importance=0.5 + self.current_emotional_state.intensity * 0.5,
            tags=list(emotion_keywords.keys())
        )
        self.emotional_memory.add_memory(memory_entry)
        
        predictions = self.behavior_predictor.get_full_prediction(
            self.current_emotional_state,
            self.personality_engine.traits,
            context,
            self.emotional_history
        )
        
        response = self.response_generator.generate_response(
            self.current_emotional_state,
            self.personality_engine.traits,
            context,
            reasoning_result
        )
        
        self.current_emotional_state = self._decay_emotions(self.current_emotional_state)
        
        return {
            'emotional_state': self.current_emotional_state.to_dict(),
            'sentiment': sentiment_result,
            'context': self.context_engine.get_context_summary(),
            'reasoning': reasoning_result,
            'predictions': predictions,
            'response': response,
            'dominant_emotion': self.current_emotional_state.get_dominant_emotion()
        }

    def _update_emotional_state(self, sentiment_result: Dict, emotion_keywords: Dict, additional_emotions: Optional[Dict]):
        sentiment = sentiment_result['sentiment']
        intensity = sentiment_result['intensity']
        
        if sentiment > 0:
            self.current_emotional_state.primary_emotions['happiness'] = min(1.0, 
                self.current_emotional_state.primary_emotions['happiness'] + sentiment * 0.3)
        else:
            self.current_emotional_state.primary_emotions['sadness'] = min(1.0,
                self.current_emotional_state.primary_emotions['sadness'] + abs(sentiment) * 0.3)
        
        for emotion, keywords in emotion_keywords.items():
            if keywords:
                boost = min(0.8, len(keywords) * 0.2)
                if emotion in self.current_emotional_state.primary_emotions:
                    self.current_emotional_state.primary_emotions[emotion] = min(1.0,
                        self.current_emotional_state.primary_emotions[emotion] + boost)
                elif emotion in self.current_emotional_state.secondary_emotions:
                    self.current_emotional_state.secondary_emotions[emotion] = min(1.0,
                        self.current_emotional_state.secondary_emotions[emotion] + boost)
                elif emotion in self.current_emotional_state.advanced_emotions:
                    self.current_emotional_state.advanced_emotions[emotion] = min(1.0,
                        self.current_emotional_state.advanced_emotions[emotion] + boost)
        
        if additional_emotions:
            for emotion, value in additional_emotions.items():
                if emotion in self.current_emotional_state.primary_emotions:
                    self.current_emotional_state.primary_emotions[emotion] = max(0.0, min(1.0, value))
                elif emotion in self.current_emotional_state.secondary_emotions:
                    self.current_emotional_state.secondary_emotions[emotion] = max(0.0, min(1.0, value))
                elif emotion in self.current_emotional_state.advanced_emotions:
                    self.current_emotional_state.advanced_emotions[emotion] = max(0.0, min(1.0, value))
        
        self.current_emotional_state.intensity = intensity
        
        self.current_emotional_state = self.personality_engine.influence_emotional_state(self.current_emotional_state)

    def _apply_reasoning_to_emotions(self, reasoning_result: Dict):
        bayesian = reasoning_result.get('bayesian_updated', {})
        for emotion, value in bayesian.items():
            if emotion in self.current_emotional_state.primary_emotions:
                self.current_emotional_state.primary_emotions[emotion] = (
                    self.current_emotional_state.primary_emotions[emotion] * 0.7 + value * 0.3
                )
            elif emotion in self.current_emotional_state.secondary_emotions:
                self.current_emotional_state.secondary_emotions[emotion] = (
                    self.current_emotional_state.secondary_emotions[emotion] * 0.7 + value * 0.3
                )
            elif emotion in self.current_emotional_state.advanced_emotions:
                self.current_emotional_state.advanced_emotions[emotion] = (
                    self.current_emotional_state.advanced_emotions[emotion] * 0.7 + value * 0.3
                )

    def _decay_emotions(self, state: EmotionalState) -> EmotionalState:
        decay_factor = 0.85
        new_state = EmotionalState()
        
        for emotion, value in state.primary_emotions.items():
            new_state.primary_emotions[emotion] = value * decay_factor
        
        for emotion, value in state.secondary_emotions.items():
            new_state.secondary_emotions[emotion] = value * decay_factor
        
        for emotion, value in state.advanced_emotions.items():
            new_state.advanced_emotions[emotion] = value * decay_factor
        
        new_state.intensity = state.intensity * decay_factor
        
        return new_state

    def get_emotional_state(self) -> Dict:
        return self.current_emotional_state.to_dict()

    def get_personality(self) -> Dict:
        return self.personality_engine.get_traits()

    def get_memory_summary(self) -> Dict:
        return {
            'short_term_count': len(self.emotional_memory.short_term_memory),
            'long_term_count': len(self.emotional_memory.long_term_memory),
            'recent_emotions': self.emotional_memory.emotional_patterns
        }

    def reset(self):
        self.current_emotional_state = EmotionalState()
        self.emotional_history = []
        self.emotional_memory = EmotionalMemory()
        self.context_engine = ContextEngine()
        self.reasoning_engine.state_machine.reset()
        self.interaction_count = 0
