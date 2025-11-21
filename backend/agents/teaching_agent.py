
"""
Teaching Agent - Autonomous content generation and delivery
"""
from agents.base_agent import BaseAgent
from llm_service import LLMService
from datetime import datetime  # ADD THIS LINE
import random


class TeachingAgent(BaseAgent):
    """
    Autonomous agent responsible for:
    - Generating personalized lessons
    - Adapting teaching style
    - Selecting examples based on student performance
    """
    
    def __init__(self):
        super().__init__("TA-001", "TeachingAgent")
        self.llm_service = LLMService()
        self.teaching_styles = ["visual", "practical", "theoretical", "example-driven"]
        self.current_style = "practical"
        self.lessons_generated = 0
        
    def perceive(self, environment):
        """
        Perceive student state from environment
        
        Args:
            environment: dict with {
                'user_id': int,
                'topic_id': int,
                'knowledge_level': float,
                'learning_history': list,
                'preferred_style': str (optional)
            }
        """
        self.update_state("perceiving")
        self.log(f"Perceiving environment for user {environment.get('user_id')}")
        
        self.user_id = environment.get('user_id')
        self.topic_id = environment.get('topic_id')
        self.knowledge_level = environment.get('knowledge_level', 0.0)
        self.learning_history = environment.get('learning_history', [])
        self.preferred_style = environment.get('preferred_style')
        
        # Analyze learning patterns
        self.analyze_learning_patterns()
        
        return self
    
    def analyze_learning_patterns(self):
        """Autonomous analysis of learning history"""
        if len(self.learning_history) > 3:
            # Detect if student struggles with theory
            theory_struggles = sum(1 for h in self.learning_history 
                                  if h.get('type') == 'theory' and not h.get('success'))
            
            if theory_struggles > 2:
                self.log("Detected struggle with theoretical content")
                self.current_style = "practical"
            else:
                self.current_style = "theoretical"
        
        self.log(f"Selected teaching style: {self.current_style}")
    
    def decide(self):
        """
        Autonomous decision making:
        - Which teaching style to use?
        - How detailed should the lesson be?
        - What examples to include?
        """
        self.update_state("deciding")
        
        # Decision 1: Lesson complexity
        if self.knowledge_level < 0.3:
            self.lesson_complexity = "simple"
            self.example_count = 3
        elif self.knowledge_level < 0.7:
            self.lesson_complexity = "moderate"
            self.example_count = 2
        else:
            self.lesson_complexity = "advanced"
            self.example_count = 1
        
        # Decision 2: Teaching approach
        if self.current_style == "practical":
            self.focus = "hands-on examples and real-world applications"
        elif self.current_style == "theoretical":
            self.focus = "core concepts and underlying principles"
        else:
            self.focus = "balanced theory and practice"
        
        # Decision 3: Motivational elements
        if self.knowledge_level > 0.8:
            self.motivation = "challenge the student with advanced concepts"
        elif self.knowledge_level < 0.2:
            self.motivation = "encourage with achievable goals"
        else:
            self.motivation = "maintain momentum with progressive difficulty"
        
        self.log(f"Decisions: complexity={self.lesson_complexity}, "
                f"examples={self.example_count}, focus={self.focus}")
        
        return self
    
    def act(self):
        """
        Execute: Generate the lesson
        """
        self.update_state("acting")
        self.log("Generating personalized lesson...")
        
        # Get topic details
        from models import Topic
        topic = Topic.query.get(self.topic_id)
        
        if not topic:
            self.log("Topic not found", "error")
            return {"error": "Topic not found"}
        
        # Construct adaptive prompt
        prompt = f"""
        You are an expert teacher specializing in {self.current_style} teaching.
        
        STUDENT PROFILE:
        - Current knowledge level: {self.knowledge_level*100:.0f}%
        - Preferred learning: {self.focus}
        - Motivation strategy: {self.motivation}
        
        TASK: Create a {self.lesson_complexity} lesson on "{topic.name}"
        
        REQUIREMENTS:
        1. Start with a compelling hook
        2. Include {self.example_count} {self.current_style} examples
        3. Use {self.lesson_complexity} language
        4. Focus on {self.focus}
        5. End with a practice challenge
        
        STRUCTURE:
        ## Introduction
        Hook the student with why this matters
        
        ## Core Concepts
        Explain key ideas with {self.current_style} approach
        
        ## Practical Examples
        Provide {self.example_count} clear examples with code
        
        ## Real-World Applications
        Show where this is used professionally
        
        ## Key Takeaways
        3-5 bullet points
        
        ## Practice Challenge
        One coding exercise matching {self.lesson_complexity} level
        
        Keep paragraphs short. Use **bold** for key terms.
        Use code blocks with ```python.
        Total: 400-600 words.
        """
        
        try:
            # Generate lesson
            lesson_content = self.llm_service.generate_lesson_with_prompt(
                topic.name,
                topic.difficulty,
                self.knowledge_level,
                custom_prompt=prompt
            )
            
            self.lessons_generated += 1
            self.log(f"Lesson generated successfully (Total: {self.lessons_generated})")
            
            # Store in agent memory
            self.memory.append({
                "action": "lesson_generated",
                "topic": topic.name,
                "style": self.current_style,
                "complexity": self.lesson_complexity,
                "user_id": self.user_id
            })
            
            self.update_state("completed")
            
            return {
                "content": lesson_content,
                "metadata": {
                    "teaching_style": self.current_style,
                    "complexity": self.lesson_complexity,
                    "example_count": self.example_count,
                    "agent": self.name,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.log(f"Error generating lesson: {str(e)}", "error")
            self.update_state("error")
            return {"error": str(e)}
    
    def get_statistics(self):
        """Return agent statistics"""
        return {
            "agent": self.name,
            "lessons_generated": self.lessons_generated,
            "current_style": self.current_style,
            "state": self.state,
            "memory_size": len(self.memory)
        }