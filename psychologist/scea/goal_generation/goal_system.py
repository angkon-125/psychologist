from scea.core.models import Goal, Need
from typing import Dict, List
import random


class GoalGenerationEngine:
    def __init__(self):
        self.active_goals: List[Goal] = []
        self.completed_goals: List[Goal] = []
        self.abandoned_goals: List[Goal] = []
        self.goal_templates = {
            'knowledge': [
                "Learn about {topic}",
                "Understand how {thing} works",
                "Discover new information about {subject}"
            ],
            'social': [
                "Connect with {entity}",
                "Build a stronger relationship with {entity}",
                "Collaborate on something with {entity}"
            ],
            'achievement': [
                "Accomplish {task}",
                "Complete {project} successfully",
                "Reach {milestone}"
            ],
            'exploration': [
                "Explore {area}",
                "Discover what's in {place}",
                "Try {new_activity}"
            ],
            'stability': [
                "Secure {resource}",
                "Establish routine for {activity}",
                "Create backup for {asset}"
            ]
        }

    def generate_goals(
        self,
        needs: Dict[str, Need],
        emotions: Dict,
        world_model: Dict
    ) -> List[Goal]:
        new_goals = []
        
        sorted_needs = sorted(
            needs.values(),
            key=lambda x: x.priority * (1 + x.deprivation),
            reverse=True
        )[:3]
        
        for need in sorted_needs:
            if need.satisfaction < 0.6:
                goal = self._create_goal_for_need(need, emotions, world_model)
                if goal:
                    new_goals.append(goal)
        
        if emotions.get('curiosity', 0) > 0.6:
            goal = self._create_goal_for_need(
                Need(name='exploration', priority=0.7),
                emotions,
                world_model
            )
            if goal:
                new_goals.append(goal)
        
        for goal in new_goals:
            existing = [g for g in self.active_goals if g.description == goal.description]
            if not existing:
                self.active_goals.append(goal)
        
        self._update_goal_progress()
        self._cleanup_goals()
        
        return new_goals

    def _create_goal_for_need(
        self,
        need: Need,
        emotions: Dict,
        world_model: Dict
    ) -> Goal:
        templates = self.goal_templates.get(need.name, self.goal_templates['knowledge'])
        template = random.choice(templates)
        
        context = world_model.get('environment_state', {})
        topic = context.get('current_topic', 'something')
        entity = context.get('current_entity', 'someone')
        
        description = template.format(
            topic=topic,
            thing=topic,
            subject=topic,
            entity=entity,
            task='a task',
            project='a project',
            milestone='a milestone',
            area='an area',
            place='a place',
            new_activity='a new activity',
            resource='a resource',
            activity='an activity',
            asset='an asset'
        )
        
        return Goal(
            description=description,
            priority=need.priority,
            progress=0.0,
            status='pending'
        )

    def _update_goal_progress(self):
        for goal in self.active_goals:
            if goal.progress < 1.0:
                goal.progress += 0.01
                if goal.progress >= 1.0:
                    goal.status = 'completed'

    def _cleanup_goals(self):
        completed = [g for g in self.active_goals if g.status == 'completed']
        abandoned = [g for g in self.active_goals if g.status == 'abandoned']
        
        self.completed_goals.extend(completed)
        self.abandoned_goals.extend(abandoned)
        
        self.active_goals = [
            g for g in self.active_goals
            if g.status not in ['completed', 'abandoned']
        ]
        
        if len(self.active_goals) > 10:
            self.active_goals = sorted(
                self.active_goals,
                key=lambda x: x.priority,
                reverse=True
            )[:10]

    def get_highest_priority_goal(self) -> Goal:
        if not self.active_goals:
            return None
        return max(self.active_goals, key=lambda x: x.priority)
