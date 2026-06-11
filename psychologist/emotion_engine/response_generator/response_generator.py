from ..models import EmotionalState, PersonalityTraits, ConversationContext
from typing import Dict, List
import random


class ResponseGenerator:
    def __init__(self):
        self.response_templates = self._init_templates()

    def _init_templates(self) -> Dict:
        return {
            'supportive': [
                "I'm here for you. It sounds like you're going through a difficult time.",
                "That must be really hard. I want you to know I care about how you're feeling.",
                "I understand this is challenging. Let's take this one step at a time together.",
                "Your feelings are valid. I'm glad you're sharing this with me.",
                "It takes courage to feel this deeply. I'm here to listen without judgment."
            ],
            'calming': [
                "Let's take a deep breath together. We can get through this.",
                "I hear how intense this feels. Let's find some calm together.",
                "Your feelings are valid, and we'll work through this patiently.",
                "Let's pause for a moment. Everything will be okay.",
                "I'm here with you. Let's focus on what we can control right now."
            ],
            'reassuring': [
                "You're not alone in this. I believe in your strength.",
                "It's okay to feel this way. We'll face this together.",
                "You've handled hard things before, and you can handle this too.",
                "I have confidence in your ability to navigate this.",
                "This feeling is temporary, but your resilience is permanent."
            ],
            'celebratory': [
                "That's wonderful! I'm so happy for you!",
                "What great news! You deserve to celebrate this!",
                "That's absolutely fantastic! Well done!",
                "I love hearing this! You should be proud!",
                "This is amazing! Let's celebrate this moment!"
            ],
            'encouraging': [
                "That's a great direction to explore! I'm excited to see where this goes.",
                "Your curiosity is inspiring! Keep following that interest.",
                "This is a wonderful opportunity! I believe in you.",
                "I love your enthusiasm! Let's explore this together.",
                "You're onto something great here! Keep going!"
            ],
            'stress_relief': [
                "Let's focus on what we can do right now to ease this stress.",
                "Taking time for yourself is so important. What usually helps you relax?",
                "Let's break this down into smaller, manageable parts.",
                "Remember to be kind to yourself right now.",
                "You're carrying a lot. Let's find ways to lighten the load together."
            ],
            'recovery': [
                "Your well-being comes first. Let's prioritize rest and recovery.",
                "It's okay to step back and care for yourself.",
                "Recovery is a process, not a race. Be patient with yourself.",
                "Let's focus on healing together. Small steps count.",
                "You don't have to push through everything right now."
            ],
            'trust_building': [
                "I value our connection and want you to feel safe with me.",
                "Your trust means a lot to me. I'm here consistently.",
                "I'm committed to being open and honest with you.",
                "You can share anything with me in confidence.",
                "Building trust takes time, and I'm here for the long haul."
            ],
            'neutral': [
                "I understand. Tell me more about that.",
                "That's interesting. Can you share more?",
                "I'm listening. What else is on your mind?",
                "Thank you for sharing that with me.",
                "I appreciate you opening up."
            ]
        }

    def generate_response(self, emotional_state: EmotionalState, personality: PersonalityTraits, context: ConversationContext, reasoning_result: Dict) -> str:
        mode = reasoning_result.get('mode', 'neutral')
        templates = self.response_templates.get(mode, self.response_templates['neutral'])
        
        base_response = random.choice(templates)
        
        personalized = self._personalize_response(base_response, emotional_state, personality, context)
        
        return personalized

    def _personalize_response(self, response: str, emotional_state: EmotionalState, personality: PersonalityTraits, context: ConversationContext) -> str:
        dominant = emotional_state.get_dominant_emotion()
        
        context_topic = context.topic
        if context_topic and context_topic != 'general':
            topic_additions = {
                'work': " How is work affecting you right now?",
                'family': " Family relationships can be so complex.",
                'health': " Your health is so important.",
                'relationships': " Relationships are such a big part of our lives.",
                'education': " Learning and growth matter so much.",
                'finance': " Finances can be really stressful.",
                'hobbies': " It's great you have things you enjoy!"
            }
            if context_topic in topic_additions:
                response += topic_additions[context_topic]
        
        if personality.extraversion > 0.7:
            extro_add = " I'd love to hear more about your experiences!"
            if "!" in response:
                response = response.replace("!", extro_add + "!", 1)
        
        if personality.extraversion < 0.3:
            response += " Take all the time you need to share."
        
        return response

    def generate_multiple_responses(self, emotional_state: EmotionalState, personality: PersonalityTraits, context: ConversationContext, reasoning_result: Dict, count: int = 3) -> List[str]:
        responses = []
        for _ in range(count):
            responses.append(self.generate_response(emotional_state, personality, context, reasoning_result))
        return responses

    def get_response_style(self, mode: str) -> List[str]:
        return self.response_templates.get(mode, self.response_templates['neutral'])
