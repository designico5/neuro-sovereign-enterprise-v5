#!/usr/bin/env python3
#===============================================================================
# MULTI-AGENT ORCHESTRATION SYSTEM
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Coordinate multiple AI agents with intelligent routing
#===============================================================================

import os
import json
import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import uuid

class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    PROCESSING = "processing"

class AgentPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AgentTask:
    id: str
    description: str
    required_capabilities: List[str]
    priority: AgentPriority
    context: Dict
    callback: Optional[Callable] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class AgentResponse:
    task_id: str
    agent_id: str
    success: bool
    result: Dict
    error: Optional[str] = None
    processing_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class AIAgent:
    """Base AI Agent class"""
    
    def __init__(self, agent_id: str, config: Dict, ai_provider_manager):
        self.agent_id = agent_id
        self.config = config
        self.ai_provider_manager = ai_provider_manager
        self.status = AgentStatus.IDLE
        self.current_task = None
        self.performance_metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_processing_time": 0.0,
            "success_rate": 1.0
        }
    
    def can_handle_task(self, task: AgentTask) -> bool:
        """Check if agent can handle the task"""
        required = set(task.required_capabilities)
        available = set(self.config.get("capabilities", []))
        return required.issubset(available)
    
    async def process_task(self, task: AgentTask) -> AgentResponse:
        """Process a task"""
        self.status = AgentStatus.PROCESSING
        self.current_task = task
        task.started_at = datetime.now()
        
        try:
            # Select appropriate AI provider and model
            provider = self.config.get("ai_provider", "ollama_local")
            model = self.config.get("model", "llama3.1:8b")
            
            # Process task using AI provider
            result = await self._execute_with_ai(task, provider, model)
            
            # Update metrics
            self.performance_metrics["tasks_completed"] += 1
            processing_time = (datetime.now() - task.started_at).total_seconds()
            self._update_avg_processing_time(processing_time)
            
            # Update status
            self.status = AgentStatus.IDLE
            self.current_task = None
            task.completed_at = datetime.now()
            
            return AgentResponse(
                task_id=task.id,
                agent_id=self.agent_id,
                success=True,
                result=result,
                processing_time=processing_time
            )
            
        except Exception as e:
            # Update error metrics
            self.performance_metrics["tasks_failed"] += 1
            self.status = AgentStatus.ERROR
            self.current_task = None
            
            return AgentResponse(
                task_id=task.id,
                agent_id=self.agent_id,
                success=False,
                result={},
                error=str(e)
            )
    
    async def _execute_with_ai(self, task: AgentTask, provider: str, model: str) -> Dict:
        """Execute task using AI provider"""
        # This would integrate with the AI provider manager
        # For now, return a simulated response
        return {
            "agent_id": self.agent_id,
            "task_description": task.description,
            "provider": provider,
            "model": model,
            "analysis": f"Processed by {self.agent_id}",
            "confidence": 0.95
        }
    
    def _update_avg_processing_time(self, new_time: float):
        """Update average processing time"""
        total_tasks = self.performance_metrics["tasks_completed"]
        current_avg = self.performance_metrics["avg_processing_time"]
        self.performance_metrics["avg_processing_time"] = (
            (current_avg * (total_tasks - 1) + new_time) / total_tasks
        )
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        total = self.performance_metrics["tasks_completed"] + self.performance_metrics["tasks_failed"]
        success_rate = (
            self.performance_metrics["tasks_completed"] / total 
            if total > 0 else 1.0
        )
        self.performance_metrics["success_rate"] = success_rate
        
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "current_task": self.current_task.id if self.current_task else None,
            "performance": self.performance_metrics
        }

class AgentOrchestrator:
    """Multi-Agent Orchestration System"""
    
    def __init__(self, config_path: str = "layers/6_cognitive/voice_interface_config.json"):
        self.config = self.load_config(config_path)
        self.agents: Dict[str, AIAgent] = {}
        self.task_queue: List[AgentTask] = []
        self.completed_tasks: List[AgentResponse] = []
        self.ai_provider_manager = None  # Would be initialized with AIProviderManager
        self.load_agents()
        
    def load_config(self, config_path: str) -> Dict:
        """Load agent orchestration configuration"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "agent_orchestration": {
                "agents": {}
            }
        }
    
    def load_agents(self):
        """Load AI agents from configuration"""
        agents_config = self.config.get("agent_orchestration", {}).get("agents", {})
        
        for agent_id, agent_config in agents_config.items():
            if agent_config.get("enabled", True):
                agent = AIAgent(agent_id, agent_config, self.ai_provider_manager)
                self.agents[agent_id] = agent
                print(f"Loaded agent: {agent_id}")
    
    def register_agent(self, agent: AIAgent):
        """Register a new agent"""
        self.agents[agent.agent_id] = agent
        print(f"Registered agent: {agent.agent_id}")
    
    def submit_task(self, description: str, required_capabilities: List[str], 
                   priority: AgentPriority = AgentPriority.MEDIUM, 
                   context: Dict = None) -> str:
        """Submit a task to the orchestration system"""
        task = AgentTask(
            id=str(uuid.uuid4()),
            description=description,
            required_capabilities=required_capabilities,
            priority=priority,
            context=context or {}
        )
        
        # Add to queue with priority
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
        
        print(f"Task submitted: {task.id} - {description}")
        return task.id
    
    def get_available_agent(self, task: AgentTask) -> Optional[AIAgent]:
        """Find an available agent that can handle the task"""
        for agent in self.agents.values():
            if agent.status == AgentStatus.IDLE and agent.can_handle_task(task):
                return agent
        return None
    
    async def process_task_queue(self):
        """Process tasks in the queue"""
        while self.task_queue:
            task = self.task_queue.pop(0)
            
            # Find available agent
            agent = self.get_available_agent(task)
            
            if agent:
                print(f"Assigning task {task.id} to agent {agent.agent_id}")
                response = await agent.process_task(task)
                self.completed_tasks.append(response)
                
                # Execute callback if provided
                if task.callback:
                    await task.callback(response)
            else:
                # No available agent, requeue with lower priority
                print(f"No available agent for task {task.id}, requeueing")
                if task.priority.value > AgentPriority.LOW.value:
                    task.priority = AgentPriority(task.priority.value - 1)
                    self.task_queue.append(task)
                else:
                    # Task failed - no agent available
                    self.completed_tasks.append(AgentResponse(
                        task_id=task.id,
                        agent_id="none",
                        success=False,
                        result={},
                        error="No available agent"
                    ))
    
    async def execute_task(self, description: str, required_capabilities: List[str],
                         context: Dict = None) -> AgentResponse:
        """Execute a single task immediately"""
        task_id = self.submit_task(description, required_capabilities, 
                                  AgentPriority.HIGH, context)
        await self.process_task_queue()
        
        # Find the response for this task
        for response in self.completed_tasks:
            if response.task_id == task_id:
                return response
        
        return AgentResponse(
            task_id=task_id,
            agent_id="none",
            success=False,
            result={},
            error="Task not found in completed tasks"
        )
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        return {
            "total_agents": len(self.agents),
            "idle_agents": sum(1 for a in self.agents.values() if a.status == AgentStatus.IDLE),
            "busy_agents": sum(1 for a in self.agents.values() if a.status == AgentStatus.BUSY),
            "error_agents": sum(1 for a in self.agents.values() if a.status == AgentStatus.ERROR),
            "pending_tasks": len(self.task_queue),
            "completed_tasks": len(self.completed_tasks),
            "agents": {agent_id: agent.get_performance_summary() 
                      for agent_id, agent in self.agents.items()}
        }
    
    def get_task_results(self, task_id: str) -> Optional[AgentResponse]:
        """Get results for a specific task"""
        for response in self.completed_tasks:
            if response.task_id == task_id:
                return response
        return None

async def main():
    """Main entry point for testing"""
    orchestrator = AgentOrchestrator()
    
    print("Agent Orchestration System Status:")
    status = orchestrator.get_system_status()
    print(json.dumps(status, indent=2))
    
    # Test task execution
    print("\nTesting task execution...")
    response = await orchestrator.execute_task(
        description="Analyze this text for sentiment",
        required_capabilities=["natural_language_understanding"],
        context={"text": "This is a great day!"}
    )
    
    print(f"Task Response: {json.dumps(response.__dict__, indent=2, default=str)}")

if __name__ == "__main__":
    asyncio.run(main())