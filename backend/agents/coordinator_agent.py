"""
Coordinator Agent - Orchestrates all other agents
"""
from agents.base_agent import BaseAgent
from agents.teaching_agent import TeachingAgent
from agents.assessment_agent import AssessmentAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.tutor_agent import TutorAgent
from agents.recommendation_agent import RecommendationAgent
from datetime import datetime
import json

class CoordinatorAgent(BaseAgent):
    """
    Master agent that coordinates all other agents
    """
    
    def __init__(self):
        super().__init__("CA-001", "CoordinatorAgent")
        
        # Initialize all sub-agents
        self.teaching_agent = TeachingAgent()
        self.assessment_agent = AssessmentAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.tutor_agent = TutorAgent()
        self.recommendation_agent = RecommendationAgent()
        
        self.tasks_coordinated = 0
        
        self.log("Coordinator initialized with 5 sub-agents")
    
    def perceive(self, environment):
        """
        Perceive global learning environment
        """
        self.update_state("perceiving")
        self.log(f"Coordinating agents for task: {environment.get('task')}")
        
        self.task = environment.get('task')
        self.user_id = environment.get('user_id')
        self.context = environment.get('context', {})
        
        return self
    
    def decide(self):
        """
        Decide which agents to activate
        """
        self.update_state("deciding")
        
        # Route to appropriate agents based on task
        self.active_agents = []
        
        if self.task == "generate_lesson":
            self.active_agents = [self.teaching_agent, self.knowledge_agent]
            self.workflow = "sequential"  # Knowledge first, then teaching
            
        elif self.task == "generate_quiz":
            self.active_agents = [self.knowledge_agent, self.assessment_agent]
            self.workflow = "sequential"
            
        elif self.task == "evaluate_answer":
            self.active_agents = [self.assessment_agent, self.knowledge_agent]
            self.workflow = "sequential"
            
        elif self.task == "provide_hint":
            self.active_agents = [self.tutor_agent]
            self.workflow = "single"
            
        elif self.task == "recommend_topic":
            self.active_agents = [self.knowledge_agent, self.recommendation_agent]
            self.workflow = "sequential"
            
        elif self.task == "full_learning_session":
            # Complex workflow involving all agents
            self.active_agents = [
                self.knowledge_agent,
                self.recommendation_agent,
                self.teaching_agent,
                self.assessment_agent,
                self.tutor_agent
            ]
            self.workflow = "complex"
        
        else:
            self.log(f"Unknown task: {self.task}", "warning")
            self.active_agents = []
            self.workflow = "none"
        
        self.log(f"Activating {len(self.active_agents)} agents in {self.workflow} workflow")
        
        return self
    
    def act(self):
        """
        Execute coordinated agent workflow
        """
        self.update_state("acting")
        self.log("Executing coordinated workflow...")
        
        results = {}
        
        try:
            if self.workflow == "single":
                # Single agent execution
                agent = self.active_agents[0]
                agent.perceive(self.context)
                agent.decide()
                results = agent.act()
                
            elif self.workflow == "sequential":
                # Sequential agent execution
                for i, agent in enumerate(self.active_agents):
                    self.log(f"Step {i+1}: Executing {agent.name}")
                    
                    # Each agent gets results from previous
                    context = {**self.context, **results}
                    
                    agent.perceive(context)
                    agent.decide()
                    agent_result = agent.act()
                    
                    results[agent.name] = agent_result
                
            elif self.workflow == "complex":
                # Complex multi-agent orchestration
                results = self._execute_complex_workflow()
            
            self.tasks_coordinated += 1
            self.log(f"Workflow completed successfully (Total tasks: {self.tasks_coordinated})")
            
            self.update_state("completed")
            
            return {
                "success": True,
                "results": results,
                "agents_used": [a.name for a in self.active_agents],
                "workflow": self.workflow,
                "coordinator": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.log(f"Workflow error: {str(e)}", "error")
            self.update_state("error")
            return {
                "success": False,
                "error": str(e),
                "coordinator": self.name
            }
    
    def _execute_complex_workflow(self):
        """
        Execute complex multi-agent workflow
        """
        results = {}
        
        # Step 1: Knowledge Agent analyzes current state
        self.log("Complex workflow - Step 1: Knowledge analysis")
        self.knowledge_agent.perceive({
            'user_id': self.user_id,
            'recent_activities': self.context.get('recent_activities', [])
        })
        self.knowledge_agent.decide()
        knowledge_result = self.knowledge_agent.act()
        results['knowledge_analysis'] = knowledge_result
        
        # Step 2: Recommendation Agent suggests path
        self.log("Complex workflow - Step 2: Path recommendation")
        self.recommendation_agent.perceive({
            'user_id': self.user_id,
            'current_topic_id': self.context.get('current_topic_id')
        })
        self.recommendation_agent.decide()
        recommendation_result = self.recommendation_agent.act()
        results['recommendations'] = recommendation_result
        
        # Step 3: Teaching Agent creates lesson
        if recommendation_result.get('next_best'):
            next_topic = recommendation_result['next_best']
            
            self.log("Complex workflow - Step 3: Lesson generation")
            self.teaching_agent.perceive({
                'user_id': self.user_id,
                'topic_id': next_topic['topic_id'],
                'knowledge_level': next_topic['current_knowledge'],
                'learning_history': []
            })
            self.teaching_agent.decide()
            teaching_result = self.teaching_agent.act()
            results['lesson'] = teaching_result
        
        # Step 4: Assessment Agent prepares quiz
        self.log("Complex workflow - Step 4: Assessment preparation")
        self.assessment_agent.perceive({
            'user_id': self.user_id,
            'topic_id': self.context.get('topic_id'),
            'knowledge_level': knowledge_result.get('predicted_growth', 0.5),
            'recent_performance': []
        })
        self.assessment_agent.decide()
        assessment_result = self.assessment_agent.act()
        results['assessment'] = assessment_result
        
        # Step 5: Tutor Agent provides initial guidance
        self.log("Complex workflow - Step 5: Tutoring setup")
        motivation = self.tutor_agent.provide_motivation({
            'score': 0.5,
            'improvement': 0.1
        })
        results['motivation'] = motivation
        
        return results
    
    def get_agent_status(self):
        """
        Get status of all agents
        """
        return {
            "coordinator": self.get_statistics(),
            "sub_agents": {
                "teaching": self.teaching_agent.get_statistics(),
                "assessment": self.assessment_agent.get_statistics(),
                "knowledge": self.knowledge_agent.get_statistics(),
                "tutor": self.tutor_agent.get_statistics(),
                "recommendation": self.recommendation_agent.get_statistics()
            },
            "total_memory": sum([
                len(self.teaching_agent.memory),
                len(self.assessment_agent.memory),
                len(self.knowledge_agent.memory),
                len(self.tutor_agent.memory),
                len(self.recommendation_agent.memory)
            ])
        }
    
    def get_statistics(self):
        """Return coordinator statistics"""
        return {
            "agent": self.name,
            "tasks_coordinated": self.tasks_coordinated,
            "state": self.state,
            "active_sub_agents": len(self.active_agents) if hasattr(self, 'active_agents') else 0,
            "memory_size": len(self.memory)
        }