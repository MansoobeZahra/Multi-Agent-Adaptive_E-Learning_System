"""
Tutor Agent - Autonomous assistance and motivation
"""
from agents.base_agent import BaseAgent
from llm_service import LLMService
from datetime import datetime

class TutorAgent(BaseAgent):
    """
    Autonomous agent responsible for:
    - Providing hints
    - Answering questions
    - Motivational support
    - Adaptive guidance
    """
    
    def __init__(self):
        super().__init__("TUA-001", "TutorAgent")
        self.llm_service = LLMService()
        self.hints_provided = 0
        self.questions_answered = 0
        self.motivation_level = "neutral"
        
    def perceive(self, environment):
        """
        Perceive student's help needs
        
        Args:
            environment: dict with {
                'user_id': int,
                'question': str,
                'context': dict,
                'frustration_level': str (optional)
            }
        """
        self.update_state("perceiving")
        self.log(f"Perceiving help request from user {environment.get('user_id')}")
        
        self.user_id = environment.get('user_id')
        self.question = environment.get('question')
        self.context = environment.get('context', {})
        self.frustration_level = environment.get('frustration_level', 'normal')
        
        return self
    
    def decide(self):
        """
        Autonomous decisions:
        - How much help to provide?
        - What teaching approach?
        - Level of motivation needed?
        """
        self.update_state("deciding")
        
        # Decision 1: Hint level based on frustration
        if self.frustration_level == "high":
            self.hint_level = "detailed"
            self.motivation_level = "encouraging"
        elif self.frustration_level == "low":
            self.hint_level = "subtle"
            self.motivation_level = "challenging"
        else:
            self.hint_level = "moderate"
            self.motivation_level = "supportive"
        
        # Decision 2: Response style
        attempts = self.context.get('attempt_count', 1)
        
        if attempts == 1:
            self.response_style = "guiding"
        elif attempts < 3:
            self.response_style = "explaining"
        else:
            self.response_style = "showing"  # More explicit help
        
        self.log(f"Decisions: hint_level={self.hint_level}, "
                f"style={self.response_style}, motivation={self.motivation_level}")
        
        return self
    
    def act(self):
        """
        Execute: Provide intelligent hint or answer
        """
        self.update_state("acting")
        self.log("Generating personalized assistance...")
        
        # Build adaptive prompt
        prompt = f"""
        You are a supportive programming tutor.
        
        STUDENT CONTEXT:
        - Question: {self.question}
        - Challenge: {self.context.get('challenge', 'General learning')}
        - Previous attempts: {self.context.get('attempt_count', 1)}
        - Frustration level: {self.frustration_level}
        
        YOUR APPROACH:
        - Hint level: {self.hint_level}
        - Response style: {self.response_style}
        - Motivation: {self.motivation_level}
        
        INSTRUCTIONS:
        """
        
        if self.hint_level == "subtle":
            prompt += "Provide a gentle nudge without revealing the solution. Ask guiding questions."
        elif self.hint_level == "moderate":
            prompt += "Explain the concept and provide a partial solution or approach."
        else:  # detailed
            prompt += "Provide clear explanation with example code, but encourage student to try."
        
        prompt += f"\n\nBe {self.motivation_level}. Keep response 2-4 sentences."
        
        try:
            response = self.llm_service.model.generate_content(prompt).text
            
            self.hints_provided += 1
            self.log(f"Hint provided (Total: {self.hints_provided})")
            
            # Store in memory
            self.memory.append({
                "action": "hint_provided",
                "question": self.question,
                "hint_level": self.hint_level,
                "user_id": self.user_id
            })
            
            self.update_state("completed")
            
            return {
                "hint": response,
                "hint_level": self.hint_level,
                "motivation": self.motivation_level,
                "agent": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.log(f"Error generating hint: {str(e)}", "error")
            self.update_state("error")
            return {
                "hint": "Think about what you've learned. Break the problem into smaller steps!",
                "agent": self.name
            }
    
    def provide_motivation(self, user_performance):
        """
        Autonomous motivational message based on performance
        """
        self.update_state("motivating")
        
        score = user_performance.get('score', 0)
        improvement = user_performance.get('improvement', 0)
        
        if score >= 0.8:
            message = "🌟 Excellent work! You're mastering this topic. Ready for a challenge?"
        elif score >= 0.6:
            message = "👍 Good progress! Keep practicing and you'll get there."
        elif improvement > 0.1:
            message = "📈 Great improvement! Your hard work is paying off."
        else:
            message = "💪 Don't give up! Every expert was once a beginner. Take it one step at a time."
        
        self.log(f"Motivation provided for score {score}")
        
        return {
            "message": message,
            "agent": self.name,
            "tone": "encouraging"
        }
    
    def get_statistics(self):
        """Return agent statistics"""
        return {
            "agent": self.name,
            "hints_provided": self.hints_provided,
            "questions_answered": self.questions_answered,
            "current_motivation_level": self.motivation_level,
            "state": self.state,
            "memory_size": len(self.memory)
        }