from scea.core.models import EmotionVector
from typing import List, Dict
import random


class ConsciousnessLayer:
    def __init__(self):
        self.global_workspace: List[Dict] = []
        self.attention_focus: str = ""
        self.active_thoughts: List[str] = []

    def process_for_consciousness(
        self,
        emotions: EmotionVector,
        needs: Dict,
        goals: List,
        simulations: List
    ) -> Dict:
        contents = []
        
        dominant_emotion = emotions.get_dominant_emotion()
        if dominant_emotion and emotions.emotions[dominant_emotion] > 0.3:
            contents.append({
                'type': 'emotion',
                'content': dominant_emotion,
                'priority': emotions.emotions[dominant_emotion]
            })
        
        for need_name, need in needs.items():
            if need.priority > 0.6 and need.deprivation > 0.3:
                contents.append({
                    'type': 'need',
                    'content': need_name,
                    'priority': need.priority * (1 + need.deprivation)
                })
        
        for goal in goals[:2]:
            contents.append({
                'type': 'goal',
                'content': goal.description,
                'priority': goal.priority
            })
        
        contents.sort(key=lambda x: x['priority'], reverse=True)
        self.global_workspace = contents[:5]
        
        if self.global_workspace:
            self.attention_focus = self.global_workspace[0]['content']
            self.active_thoughts = [c['content'] for c in self.global_workspace]
        
        return {
            'workspace_contents': self.global_workspace,
            'attention_focus': self.attention_focus,
            'active_thoughts': self.active_thoughts
        }
