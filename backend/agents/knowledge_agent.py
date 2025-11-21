"""
Knowledge Agent - Autonomous knowledge state management
"""
from agents.base_agent import BaseAgent
from knowledge_tracker import KnowledgeTracker
from models import db, KnowledgeState
import numpy as np
from datetime import datetime, timedelta

class KnowledgeAgent(BaseAgent):
    """
    Autonomous agent responsible for:
    - Tracking knowledge evolution
    - Predicting future performance
    - Identifying knowledge gaps
    - Suggesting review topics
    """
    
    def __init__(self):
        super().__init__("KA-001", "KnowledgeAgent")
        self.tracker = KnowledgeTracker()
        self.predictions_made = 0
        self.updates_performed = 0
        
    def perceive(self, environment):
        """
        Perceive student's learning state
        
        Args:
            environment: dict with {
                'user_id': int,
                'topic_id': int (optional),
                'recent_activities': list
            }
        """
        self.update_state("perceiving")
        self.log(f"Perceiving knowledge state for user {environment.get('user_id')}")
        
        self.user_id = environment.get('user_id')
        self.topic_id = environment.get('topic_id')
        self.recent_activities = environment.get('recent_activities', [])
        
        # Get all knowledge states
        self.knowledge_states = KnowledgeState.query.filter_by(
            user_id=self.user_id
        ).all()
        
        self.log(f"Found {len(self.knowledge_states)} knowledge states")
        
        return self
    
    def decide(self):
        """
        Autonomous decisions:
        - Which topics need review?
        - What's the optimal learning path?
        - Are there knowledge gaps?
        """
        self.update_state("deciding")
        
        # Decision 1: Apply forgetting curves
        topics_needing_review = []
        for state in self.knowledge_states:
            days_since_practice = (datetime.utcnow() - state.last_practiced).days
            
            if days_since_practice > 7 and state.knowledge_level > 0.3:
                topics_needing_review.append({
                    'topic_id': state.topic_id,
                    'days_since': days_since_practice,
                    'current_level': state.knowledge_level,
                    'priority': days_since_practice * (1 - state.knowledge_level)
                })
        
        # Sort by priority
        topics_needing_review.sort(key=lambda x: x['priority'], reverse=True)
        self.review_recommendations = topics_needing_review[:3]
        
        # Decision 2: Identify knowledge gaps
        self.knowledge_gaps = [
            state for state in self.knowledge_states
            if 0 < state.knowledge_level < 0.4
        ]
        
        # Decision 3: Predict next knowledge level
        if self.topic_id:
            self.predicted_next_level = self._predict_knowledge_growth(self.topic_id)
        else:
            self.predicted_next_level = None
        
        self.log(f"Decisions: {len(self.review_recommendations)} topics need review, "
                f"{len(self.knowledge_gaps)} knowledge gaps found")
        
        return self
    
    def _predict_knowledge_growth(self, topic_id):
        """Predict knowledge growth based on learning patterns"""
        state = KnowledgeState.query.filter_by(
            user_id=self.user_id,
            topic_id=topic_id
        ).first()
        
        if not state:
            return 0.15  # Expected growth for new topic
        
        # Predict based on practice frequency and current level
        if state.practice_count > 5:
            # Experienced learner - slower growth
            growth = 0.1 * (1 - state.knowledge_level)
        else:
            # New learner - faster initial growth
            growth = 0.15 * (1 - state.knowledge_level)
        
        predicted = min(1.0, state.knowledge_level + growth)
        self.predictions_made += 1
        
        self.log(f"Predicted knowledge growth: {state.knowledge_level:.2f} → {predicted:.2f}")
        
        return predicted
    
    def act(self):
        """
        Execute: Update knowledge states and provide recommendations
        """
        self.update_state("acting")
        self.log("Updating knowledge states...")
        
        # Apply forgetting curves to all states
        updated_states = []
        for state in self.knowledge_states:
            days_since = (datetime.utcnow() - state.last_practiced).days
            
            if days_since > 0:
                # Apply exponential forgetting
                forgetting_factor = np.exp(-0.05 * days_since)
                old_level = state.knowledge_level
                state.knowledge_level *= forgetting_factor
                
                if abs(old_level - state.knowledge_level) > 0.01:
                    updated_states.append({
                        'topic_id': state.topic_id,
                        'old_level': old_level,
                        'new_level': state.knowledge_level,
                        'decay': old_level - state.knowledge_level
                    })
                    self.updates_performed += 1
        
        # Commit updates
        db.session.commit()
        
        self.log(f"Updated {len(updated_states)} knowledge states")
        self.update_state("completed")
        
        return {
            "review_recommendations": self.review_recommendations,
            "knowledge_gaps": [
                {
                    'topic_id': gap.topic_id,
                    'level': gap.knowledge_level,
                    'confidence': gap.confidence
                }
                for gap in self.knowledge_gaps
            ],
            "predicted_growth": self.predicted_next_level,
            "updated_states": updated_states,
            "agent": self.name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def update_knowledge_from_quiz(self, topic_id, is_correct, difficulty):
        """
        Autonomous knowledge update based on quiz performance
        """
        self.update_state("updating")
        self.log(f"Updating knowledge for topic {topic_id}, correct={is_correct}")
        
        # Use existing tracker but with agent logging
        state = self.tracker.update_knowledge(
            self.user_id,
            topic_id,
            is_correct,
            difficulty
        )
        
        self.updates_performed += 1
        self.log(f"Knowledge updated: {state.knowledge_level:.2f}, "
                f"confidence: {state.confidence:.2f}")
        
        return {
            "new_level": state.knowledge_level,
            "confidence": state.confidence,
            "practice_count": state.practice_count,
            "agent": self.name
        }
    
    def get_statistics(self):
        """Return agent statistics"""
        return {
            "agent": self.name,
            "predictions_made": self.predictions_made,
            "updates_performed": self.updates_performed,
            "state": self.state,
            "memory_size": len(self.memory)
        }