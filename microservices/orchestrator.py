"""
Microservice Agent Orchestrator
Manages agent lifecycle, communication, and workflow coordination
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor
import threading

from .agent_registry import MicroServiceAgentRegistry, MicroAgentConfig

logger = logging.getLogger(__name__)

@dataclass
class TaskRequest:
    """Request for a microservice agent to perform a task"""
    task_id: str
    agent_name: str
    instruction: str
    context: Dict[str, Any] = None
    priority: int = 1
    timeout: int = 300  # 5 minutes default
    callback: Optional[Callable] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class TaskResult:
    """Result from a microservice agent task"""
    task_id: str
    agent_name: str
    status: str  # success, error, timeout
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    completed_at: str = None
    
    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.now().isoformat()

class MicroServiceOrchestrator:
    """
    Orchestrates microservice agents for complex workflows
    """
    
    def __init__(self, registry: MicroServiceAgentRegistry):
        self.registry = registry
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, TaskRequest] = {}
        self.task_results: Dict[str, TaskResult] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.running = False
        self._task_counter = 0
        self._lock = threading.Lock()
    
    def start(self):
        """Start the orchestrator"""
        self.running = True
        logger.info("Microservice orchestrator started")
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("Microservice orchestrator stopped")
    
    def generate_task_id(self) -> str:
        """Generate a unique task ID"""
        with self._lock:
            self._task_counter += 1
            return f"task_{self._task_counter}_{int(datetime.now().timestamp())}"
    
    async def submit_task(self, agent_name: str, instruction: str, 
                         context: Dict[str, Any] = None, priority: int = 1,
                         timeout: int = 300, callback: Optional[Callable] = None) -> str:
        """Submit a task to a microservice agent"""
        task_id = self.generate_task_id()
        
        task = TaskRequest(
            task_id=task_id,
            agent_name=agent_name,
            instruction=instruction,
            context=context or {},
            priority=priority,
            timeout=timeout,
            callback=callback
        )
        
        self.active_tasks[task_id] = task
        await self.task_queue.put(task)
        
        logger.info(f"Submitted task {task_id} to agent {agent_name}")
        return task_id
    
    async def execute_task(self, task: TaskRequest) -> TaskResult:
        """Execute a single task"""
        start_time = datetime.now()
        
        try:
            # Get agent configuration
            agent_config = self.registry.get_agent(task.agent_name)
            if not agent_config:
                raise ValueError(f"Agent {task.agent_name} not found")
            
            # Check if service is running
            service_status = self.registry.get_service_status(task.agent_name)
            if not service_status or service_status.get("status") != "running":
                # Try to start the service
                if not self.registry.start_service(task.agent_name):
                    raise RuntimeError(f"Failed to start service {task.agent_name}")
                service_status = self.registry.get_service_status(task.agent_name)
            
            # Execute the task
            result = await self._call_microservice(
                service_status["endpoint"], 
                task.instruction, 
                task.context,
                agent_config.prompt,
                timeout=task.timeout
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            task_result = TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                status="success",
                result=result,
                execution_time=execution_time
            )
            
        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            task_result = TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                status="timeout",
                error="Task execution timed out",
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            task_result = TaskResult(
                task_id=task.task_id,
                agent_name=task.agent_name,
                status="error",
                error=str(e),
                execution_time=execution_time
            )
        
        # Store result and cleanup
        self.task_results[task.task_id] = task_result
        if task.task_id in self.active_tasks:
            del self.active_tasks[task.task_id]
        
        # Call callback if provided
        if task.callback:
            try:
                task.callback(task_result)
            except Exception as e:
                logger.error(f"Error in task callback: {e}")
        
        logger.info(f"Task {task.task_id} completed with status: {task_result.status}")
        return task_result
    
    async def _call_microservice(self, endpoint: str, instruction: str, 
                                context: Dict[str, Any], agent_prompt: str,
                                timeout: int = 300) -> Any:
        """Call a microservice endpoint"""
        # For now, simulate microservice call
        # In a real implementation, this would make HTTP requests to the microservice
        
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Simulate different types of responses based on instruction
        if "search" in instruction.lower():
            return {
                "type": "search_results",
                "results": [
                    {"title": "Sample Result 1", "url": "http://example.com/1"},
                    {"title": "Sample Result 2", "url": "http://example.com/2"}
                ]
            }
        elif "scrape" in instruction.lower():
            return {
                "type": "scraped_content",
                "content": "Sample scraped content from the web page",
                "metadata": {"url": "http://example.com", "timestamp": datetime.now().isoformat()}
            }
        else:
            return {
                "type": "general_response",
                "response": f"Processed instruction: {instruction}",
                "context_used": bool(context)
            }
    
    async def execute_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complex workflow involving multiple microservices"""
        workflow_id = self.generate_task_id()
        workflow_results = {}
        
        logger.info(f"Starting workflow {workflow_id}")
        
        try:
            steps = workflow_config.get("steps", [])
            
            for step_idx, step in enumerate(steps):
                step_id = f"{workflow_id}_step_{step_idx}"
                agent_name = step.get("agent")
                instruction = step.get("instruction")
                depends_on = step.get("depends_on", [])
                
                # Wait for dependencies
                for dep in depends_on:
                    if dep not in workflow_results:
                        raise ValueError(f"Dependency {dep} not found for step {step_id}")
                
                # Prepare context with results from previous steps
                context = step.get("context", {})
                for dep in depends_on:
                    context[f"result_{dep}"] = workflow_results[dep]
                
                # Execute step
                task_id = await self.submit_task(
                    agent_name=agent_name,
                    instruction=instruction,
                    context=context,
                    timeout=step.get("timeout", 300)
                )
                
                # Wait for completion
                result = await self.wait_for_task(task_id)
                workflow_results[step_id] = result
                
                if result.status != "success":
                    raise RuntimeError(f"Step {step_id} failed: {result.error}")
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            return {
                "workflow_id": workflow_id,
                "status": "success",
                "results": workflow_results
            }
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e),
                "partial_results": workflow_results
            }
    
    async def wait_for_task(self, task_id: str, timeout: int = 300) -> TaskResult:
        """Wait for a task to complete"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            if task_id in self.task_results:
                return self.task_results[task_id]
            
            await asyncio.sleep(0.1)
        
        # Timeout
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        return TaskResult(
            task_id=task_id,
            agent_name="unknown",
            status="timeout",
            error="Wait timeout exceeded"
        )
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task"""
        if task_id in self.task_results:
            result = self.task_results[task_id]
            return {
                "task_id": task_id,
                "status": result.status,
                "completed": True,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time
            }
        elif task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": "running",
                "completed": False,
                "agent_name": task.agent_name,
                "created_at": task.created_at
            }
        else:
            return None
    
    def list_active_tasks(self) -> List[Dict[str, Any]]:
        """List all active tasks"""
        return [
            {
                "task_id": task.task_id,
                "agent_name": task.agent_name,
                "instruction": task.instruction[:100] + "..." if len(task.instruction) > 100 else task.instruction,
                "priority": task.priority,
                "created_at": task.created_at
            }
            for task in self.active_tasks.values()
        ]
    
    def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get task execution history"""
        results = list(self.task_results.values())
        results.sort(key=lambda x: x.completed_at, reverse=True)
        
        return [
            {
                "task_id": result.task_id,
                "agent_name": result.agent_name,
                "status": result.status,
                "execution_time": result.execution_time,
                "completed_at": result.completed_at,
                "error": result.error
            }
            for result in results[:limit]
        ]
    
    async def process_task_queue(self):
        """Process tasks from the queue (run this in a background task)"""
        while self.running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Execute task in background
                asyncio.create_task(self.execute_task(task))
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing task queue: {e}")
                await asyncio.sleep(1)

# Global orchestrator instance
orchestrator = None

def get_orchestrator(registry: MicroServiceAgentRegistry = None) -> MicroServiceOrchestrator:
    """Get or create the global orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        from .agent_registry import microservice_registry
        orchestrator = MicroServiceOrchestrator(registry or microservice_registry)
    return orchestrator