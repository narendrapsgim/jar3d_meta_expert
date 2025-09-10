"""
API Gateway for Microservice Communication
Provides RESTful API for agent management and inter-service communication
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from .agent_registry import MicroServiceAgentRegistry, MicroAgentConfig, microservice_registry
from .orchestrator import MicroServiceOrchestrator, get_orchestrator, TaskRequest

logger = logging.getLogger(__name__)

# Pydantic models for API
class AgentCreateRequest(BaseModel):
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    prompt: str = Field(..., description="Agent prompt/instructions")
    trigger_type: str = Field(default="always", description="Trigger type")
    capabilities: List[str] = Field(default=[], description="Agent capabilities")
    dependencies: List[str] = Field(default=[], description="Agent dependencies")
    container_image: Optional[str] = Field(None, description="Container image")
    environment_vars: Dict[str, str] = Field(default={}, description="Environment variables")
    resource_limits: Dict[str, Any] = Field(default={}, description="Resource limits")

class TaskSubmitRequest(BaseModel):
    agent_name: str = Field(..., description="Target agent name")
    instruction: str = Field(..., description="Task instruction")
    context: Dict[str, Any] = Field(default={}, description="Task context")
    priority: int = Field(default=1, description="Task priority")
    timeout: int = Field(default=300, description="Task timeout in seconds")

class WorkflowExecuteRequest(BaseModel):
    name: str = Field(..., description="Workflow name")
    steps: List[Dict[str, Any]] = Field(..., description="Workflow steps")
    context: Dict[str, Any] = Field(default={}, description="Workflow context")

class AgentResponse(BaseModel):
    name: str
    description: str
    trigger_type: str
    capabilities: List[str]
    dependencies: List[str]
    endpoint: Optional[str]
    container_image: Optional[str]
    created_at: str

class TaskResponse(BaseModel):
    task_id: str
    status: str
    agent_name: Optional[str] = None
    completed: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

class ServiceStatusResponse(BaseModel):
    name: str
    status: str
    endpoint: Optional[str] = None
    started_at: Optional[str] = None

# FastAPI app
app = FastAPI(
    title="Jar3d Microservice API Gateway",
    description="API Gateway for managing microservice agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection
def get_registry() -> MicroServiceAgentRegistry:
    return microservice_registry

def get_orchestrator_instance() -> MicroServiceOrchestrator:
    return get_orchestrator()

# Agent management endpoints
@app.post("/agents", response_model=AgentResponse)
async def create_agent(
    request: AgentCreateRequest,
    registry: MicroServiceAgentRegistry = Depends(get_registry)
):
    """Create a new microservice agent"""
    try:
        config = MicroAgentConfig(
            name=request.name,
            description=request.description,
            prompt=request.prompt,
            trigger_type=request.trigger_type,
            capabilities=request.capabilities,
            dependencies=request.dependencies,
            container_image=request.container_image,
            environment_vars=request.environment_vars,
            resource_limits=request.resource_limits or {"memory": "512Mi", "cpu": "0.5"}
        )
        
        success = registry.register_agent(config)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to register agent")
        
        return AgentResponse(
            name=config.name,
            description=config.description,
            trigger_type=config.trigger_type,
            capabilities=config.capabilities,
            dependencies=config.dependencies,
            endpoint=config.endpoint,
            container_image=config.container_image,
            created_at=config.created_at
        )
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    trigger_type: Optional[str] = None,
    registry: MicroServiceAgentRegistry = Depends(get_registry)
):
    """List all registered agents"""
    try:
        agents = registry.list_agents(trigger_type=trigger_type)
        return [
            AgentResponse(
                name=agent.name,
                description=agent.description,
                trigger_type=agent.trigger_type,
                capabilities=agent.capabilities,
                dependencies=agent.dependencies,
                endpoint=agent.endpoint,
                container_image=agent.container_image,
                created_at=agent.created_at
            )
            for agent in agents
        ]
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_name}", response_model=AgentResponse)
async def get_agent(
    agent_name: str,
    registry: MicroServiceAgentRegistry = Depends(get_registry)
):
    """Get a specific agent by name"""
    agent = registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        name=agent.name,
        description=agent.description,
        trigger_type=agent.trigger_type,
        capabilities=agent.capabilities,
        dependencies=agent.dependencies,
        endpoint=agent.endpoint,
        container_image=agent.container_image,
        created_at=agent.created_at
    )

@app.delete("/agents/{agent_name}")
async def delete_agent(
    agent_name: str,
    registry: MicroServiceAgentRegistry = Depends(get_registry)
):
    """Delete an agent"""
    success = registry.unregister_agent(agent_name)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {"message": f"Agent {agent_name} deleted successfully"}

# Service management endpoints
@app.post("/services/{agent_name}/start")
async def start_service(
    agent_name: str,
    registry: MicroServiceAgentRegistry = Depends(get_registry)
):
    """Start a microservice"""
    success = registry.start_service(agent_name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start service")
    
    return {"message": f"Service {agent_name} started successfully"}

@app.post("/services/{agent_name}/stop")
async def stop_service(
    agent_name: str,
    registry: MicroServiceAgentRegistry = Depends(get_registry)
):
    """Stop a microservice"""
    success = registry.stop_service(agent_name)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return {"message": f"Service {agent_name} stopped successfully"}

@app.get("/services", response_model=List[ServiceStatusResponse])
async def list_services(
    registry: MicroServiceAgentRegistry = Depends(get_registry)
):
    """List all active services"""
    services = registry.list_active_services()
    return [
        ServiceStatusResponse(
            name=name,
            status=info.get("status", "unknown"),
            endpoint=info.get("endpoint"),
            started_at=info.get("started_at")
        )
        for name, info in services.items()
    ]

@app.get("/services/{agent_name}", response_model=ServiceStatusResponse)
async def get_service_status(
    agent_name: str,
    registry: MicroServiceAgentRegistry = Depends(get_registry)
):
    """Get service status"""
    status = registry.get_service_status(agent_name)
    if not status:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return ServiceStatusResponse(
        name=agent_name,
        status=status.get("status", "unknown"),
        endpoint=status.get("endpoint"),
        started_at=status.get("started_at")
    )

# Task execution endpoints
@app.post("/tasks", response_model=Dict[str, str])
async def submit_task(
    request: TaskSubmitRequest,
    background_tasks: BackgroundTasks,
    orchestrator: MicroServiceOrchestrator = Depends(get_orchestrator_instance)
):
    """Submit a task to a microservice agent"""
    try:
        task_id = await orchestrator.submit_task(
            agent_name=request.agent_name,
            instruction=request.instruction,
            context=request.context,
            priority=request.priority,
            timeout=request.timeout
        )
        
        return {"task_id": task_id, "status": "submitted"}
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    orchestrator: MicroServiceOrchestrator = Depends(get_orchestrator_instance)
):
    """Get task status"""
    status = orchestrator.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(**status)

@app.get("/tasks", response_model=List[Dict[str, Any]])
async def list_active_tasks(
    orchestrator: MicroServiceOrchestrator = Depends(get_orchestrator_instance)
):
    """List all active tasks"""
    return orchestrator.list_active_tasks()

@app.get("/tasks/history", response_model=List[Dict[str, Any]])
async def get_task_history(
    limit: int = 100,
    orchestrator: MicroServiceOrchestrator = Depends(get_orchestrator_instance)
):
    """Get task execution history"""
    return orchestrator.get_task_history(limit=limit)

# Workflow execution endpoints
@app.post("/workflows/execute")
async def execute_workflow(
    request: WorkflowExecuteRequest,
    orchestrator: MicroServiceOrchestrator = Depends(get_orchestrator_instance)
):
    """Execute a workflow"""
    try:
        workflow_config = {
            "name": request.name,
            "steps": request.steps,
            "context": request.context
        }
        
        result = await orchestrator.execute_workflow(workflow_config)
        return result
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "jar3d-microservice-gateway"
    }

# Registry export/import endpoints
@app.get("/registry/export")
async def export_registry(
    registry: MicroServiceAgentRegistry = Depends(get_registry)
):
    """Export the entire registry"""
    return registry.export_registry()

@app.post("/registry/import")
async def import_registry(
    data: Dict[str, Any],
    registry: MicroServiceAgentRegistry = Depends(get_registry)
):
    """Import registry data"""
    try:
        registry.import_registry(data)
        return {"message": "Registry imported successfully"}
    except Exception as e:
        logger.error(f"Error importing registry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Capability-based agent discovery
@app.get("/agents/by-capability/{capability}")
async def get_agents_by_capability(
    capability: str,
    registry: MicroServiceAgentRegistry = Depends(get_registry)
):
    """Get agents by capability"""
    agents = registry.get_agents_by_capability(capability)
    return [
        AgentResponse(
            name=agent.name,
            description=agent.description,
            trigger_type=agent.trigger_type,
            capabilities=agent.capabilities,
            dependencies=agent.dependencies,
            endpoint=agent.endpoint,
            container_image=agent.container_image,
            created_at=agent.created_at
        )
        for agent in agents
    ]

class APIGateway:
    """API Gateway wrapper class"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.app = app
    
    def run(self, **kwargs):
        """Run the API gateway"""
        config = {
            "host": self.host,
            "port": self.port,
            "log_level": "info",
            **kwargs
        }
        uvicorn.run(self.app, **config)
    
    async def start_background_tasks(self):
        """Start background tasks"""
        orchestrator = get_orchestrator_instance()
        orchestrator.start()
        
        # Start task queue processor
        asyncio.create_task(orchestrator.process_task_queue())

# Global gateway instance
gateway = APIGateway()

if __name__ == "__main__":
    gateway.run()