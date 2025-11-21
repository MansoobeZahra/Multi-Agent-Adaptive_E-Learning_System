"""
Assessment Agent - Autonomous quiz generation and evaluation
"""
from agents.base_agent import BaseAgent
from llm_service import LLMService
from datetime import datetime

class AssessmentAgent(BaseAgent):
    """
    Autonomous agent responsible for:
    - Generating adaptive quizzes
    - Evaluating answers
    - Adjusting question difficulty
    - Providing detailed feedback
    """
    
    def __init__(self):
        super().__init__("AA-001", "AssessmentAgent")
        self.llm_service = LLMService()
        self.quizzes_generated = 0
        self.questions_evaluated = 0
        self.difficulty_adjustments = 0
        
    def perceive(self, environment):
        """
        Perceive student's quiz context
        
        Args:
            environment: dict with {
                'user_id': int,
                'topic_id': int,
                'knowledge_level': float,
                'recent_performance': list,
                'quiz_type': str (optional)
            }
        """
        self.update_state("perceiving")
        self.log(f"Perceiving assessment needs for user {environment.get('user_id')}")
        
        self.user_id = environment.get('user_id')
        self.topic_id = environment.get('topic_id')
        self.knowledge_level = environment.get('knowledge_level', 0.0)
        self.recent_performance = environment.get('recent_performance', [])
        self.quiz_type = environment.get('quiz_type', 'standard')
        
        return self
    
    def decide(self):
        """
        Autonomous decisions:
        - What difficulty level for questions?
        - How many questions?
        - Question types (MCQ, coding, etc.)
        - Focus areas
        """
        self.update_state("deciding")
        
        # Decision 1: Difficulty distribution
        if self.knowledge_level < 0.3:
            self.difficulty_mix = {
                'beginner': 4,
                'intermediate': 1,
                'advanced': 0
            }
        elif self.knowledge_level < 0.7:
            self.difficulty_mix = {
                'beginner': 1,
                'intermediate': 3,
                'advanced': 1
            }
        else:
            self.difficulty_mix = {
                'beginner': 0,
                'intermediate': 2,
                'advanced': 3
            }
        
        # Decision 2: Question count
        self.num_questions = sum(self.difficulty_mix.values())
        
        # Decision 3: Analyze weak areas from recent performance
        if len(self.recent_performance) > 0:
            wrong_topics = [p['topic_area'] for p in self.recent_performance 
                           if not p.get('correct')]
            if wrong_topics:
                self.focus_areas = list(set(wrong_topics))
                self.log(f"Focusing on weak areas: {self.focus_areas}")
            else:
                self.focus_areas = []
        else:
            self.focus_areas = []
        
        self.log(f"Quiz decisions: {self.difficulty_mix}, focus={self.focus_areas}")
        
        return self
    
    def act(self):
        """
        Execute: Generate adaptive quiz
        """
        self.update_state("acting")
        self.log("Generating adaptive quiz...")
        
        from models import Topic
        topic = Topic.query.get(self.topic_id)
        
        if not topic:
            self.log("Topic not found", "error")
            return {"error": "Topic not found"}
        
        # Build adaptive prompt
        focus_instruction = ""
        if self.focus_areas:
            focus_instruction = f"Focus particularly on: {', '.join(self.focus_areas)}"
        
        prompt = f"""
        Generate an adaptive quiz for "{topic.name}"
        
        STUDENT PROFILE:
        - Knowledge level: {self.knowledge_level*100:.0f}%
        - Recent weak areas: {self.focus_areas if self.focus_areas else 'None'}
        
        QUIZ STRUCTURE:
        """
        
        questions = []
        for difficulty, count in self.difficulty_mix.items():
            if count > 0:
                prompt += f"\n- {count} {difficulty} level questions"
        
        prompt += f"""
        
        {focus_instruction}
        
        Return ONLY a JSON array:
        [
          {{
            "question": "...",
            "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
            "correct_answer": "A",
            "explanation": "...",
            "difficulty": "beginner|intermediate|advanced",
            "topic_area": "specific concept being tested"
          }}
        ]
        
        NO other text. Just the JSON.
        """
        
        try:
            # Generate quiz
            quiz_questions = self.llm_service.generate_quiz_with_prompt(
                topic.name,
                self.num_questions,
                custom_prompt=prompt
            )
            
            self.quizzes_generated += 1
            self.log(f"Quiz generated successfully (Total: {self.quizzes_generated})")
            
            # Store in memory
            self.memory.append({
                "action": "quiz_generated",
                "topic": topic.name,
                "num_questions": self.num_questions,
                "difficulty_mix": self.difficulty_mix,
                "user_id": self.user_id
            })
            
            self.update_state("completed")
            
            return {
                "questions": quiz_questions,
                "metadata": {
                    "difficulty_mix": self.difficulty_mix,
                    "focus_areas": self.focus_areas,
                    "agent": self.name,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.log(f"Error generating quiz: {str(e)}", "error")
            self.update_state("error")
            return {"error": str(e)}
    
    def evaluate_answer(self, question, user_answer, correct_answer, context):
        """
        Autonomous answer evaluation with detailed feedback
        
        Args:
            question: str
            user_answer: str
            correct_answer: str
            context: dict with topic info
        """
        self.update_state("evaluating")
        self.log(f"Evaluating answer: {user_answer} vs {correct_answer}")
        
        is_correct = user_answer == correct_answer
        self.questions_evaluated += 1
        
        # Generate intelligent feedback
        feedback_prompt = f"""
        Question: {question}
        Student answered: {user_answer}
        Correct answer: {correct_answer}
        Result: {"Correct" if is_correct else "Incorrect"}
        
        Provide encouraging, educational feedback (2-3 sentences):
        1. If correct: Explain why and reinforce the concept
        2. If incorrect: Explain the misconception and guide to correct understanding
        
        Be supportive and educational.
        """
        
        try:
            feedback = self.llm_service.model.generate_content(feedback_prompt).text
        except:
            feedback = "Review the concept and try again!" if not is_correct else "Great job!"
        
        self.log(f"Answer evaluated. Correct: {is_correct}")
        
        return {
            "is_correct": is_correct,
            "feedback": feedback,
            "agent": self.name,
            "evaluated_at": datetime.utcnow().isoformat()
        }
    
    def get_statistics(self):
        """Return agent statistics"""
        return {
            "agent": self.name,
            "quizzes_generated": self.quizzes_generated,
            "questions_evaluated": self.questions_evaluated,
            "state": self.state,
            "memory_size": len(self.memory)
        }