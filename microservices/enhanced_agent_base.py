"""
Enhanced Agent Base with Microservice Integration
Extends the existing BaseAgent to work with microservice architecture
"""
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import requests
import aiohttp

from agents.agent_base import BaseAgent, ToolCallingAgent, StateT
from .agent_registry import MicroServiceAgentRegistry, MicroAgentConfig
from .orchestrator import MicroServiceOrchestrator, get_orchestrator

logger = logging.getLogger(__name__)

class MicroServiceAgent(BaseAgent[StateT]):
    """
    Agent that can communicate with microservices
    """
    
    def __init__(self, name: str, microservice_config: MicroAgentConfig, 
                 registry: MicroServiceAgentRegistry, **kwargs):
        super().__init__(name, **kwargs)
        self.microservice_config = microservice_config
        self.registry = registry
        self.orchestrator = get_orchestrator(registry)
    
    async def call_microservice(self, instruction: str, context: Dict[str, Any] = None) -> Any:
        """Call the associated microservice"""
        try:
            # Submit task to orchestrator
            task_id = await self.orchestrator.submit_task(
                agent_name=self.microservice_config.name,
                instruction=instruction,
                context=context or {}
            )
            
            # Wait for result
            result = await self.orchestrator.wait_for_task(task_id)
            
            if result.status == "success":
                return result.result
            else:
                raise RuntimeError(f"Microservice call failed: {result.error}")
                
        except Exception as e:
            logger.error(f"Error calling microservice {self.microservice_config.name}: {e}")
            raise
    
    def invoke(self, state: StateT) -> Dict[str, Any]:
        """Invoke the agent with microservice integration"""
        instructions = self.read_instructions(state)
        if not instructions:
            print(f"No instructions provided to {self.name}.")
            return state
        
        try:
            # Call microservice asynchronously
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                self.call_microservice(instructions, {"state": state})
            )
            
            # Write result to state
            self.write_to_state(state, json.dumps(result))
            
        except Exception as e:
            error_result = {"error": str(e), "agent": self.name}
            self.write_to_state(state, json.dumps(error_result))
        
        return state

class HybridAgent(ToolCallingAgent[StateT]):
    """
    Agent that can work both locally and with microservices
    """
    
    def __init__(self, name: str, microservice_config: Optional[MicroAgentConfig] = None,
                 registry: Optional[MicroServiceAgentRegistry] = None, **kwargs):
        super().__init__(name, **kwargs)
        self.microservice_config = microservice_config
        self.registry = registry
        self.orchestrator = get_orchestrator(registry) if registry else None
        self.use_microservice = microservice_config is not None
    
    async def call_microservice_async(self, instruction: str, context: Dict[str, Any] = None) -> Any:
        """Async call to microservice"""
        if not self.orchestrator or not self.microservice_config:
            raise RuntimeError("Microservice not configured")
        
        task_id = await self.orchestrator.submit_task(
            agent_name=self.microservice_config.name,
            instruction=instruction,
            context=context or {}
        )
        
        result = await self.orchestrator.wait_for_task(task_id)
        
        if result.status == "success":
            return result.result
        else:
            raise RuntimeError(f"Microservice call failed: {result.error}")
    
    def call_microservice_sync(self, instruction: str, context: Dict[str, Any] = None) -> Any:
        """Sync call to microservice"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.call_microservice_async(instruction, context)
        )
    
    def should_use_microservice(self, instruction: str) -> bool:
        """Determine whether to use microservice or local processing"""
        if not self.use_microservice:
            return False
        
        # Check if microservice has required capabilities
        if self.microservice_config:
            instruction_lower = instruction.lower()
            for capability in self.microservice_config.capabilities:
                if capability.lower() in instruction_lower:
                    return True
        
        return False
    
    def execute_tool(self, tool_response: Dict[str, Any], state: StateT) -> StateT:
        """Execute tool with microservice fallback"""
        try:
            # Try local execution first
            return self.execute_tool_local(tool_response, state)
        except Exception as e:
            logger.warning(f"Local execution failed: {e}, trying microservice")
            
            if self.use_microservice:
                try:
                    # Fallback to microservice
                    instruction = json.dumps(tool_response)
                    result = self.call_microservice_sync(instruction, {"state": state})
                    return result
                except Exception as microservice_error:
                    logger.error(f"Microservice execution also failed: {microservice_error}")
                    raise e  # Raise original error
            else:
                raise e
    
    def execute_tool_local(self, tool_response: Dict[str, Any], state: StateT) -> StateT:
        """Execute tool locally - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement execute_tool_local")

class MicroServiceMetaAgent(BaseAgent[StateT]):
    """
    Meta agent that can orchestrate multiple microservices
    """
    
    def __init__(self, name: str, registry: MicroServiceAgentRegistry, **kwargs):
        super().__init__(name, **kwargs)
        self.registry = registry
        self.orchestrator = get_orchestrator(registry)
    
    async def orchestrate_workflow(self, requirements: str, state: StateT) -> Dict[str, Any]:
        """Orchestrate a workflow using multiple microservices"""
        
        # Analyze requirements to determine needed capabilities
        needed_capabilities = self.analyze_requirements(requirements)
        
        # Find suitable agents for each capability
        workflow_steps = []
        for capability in needed_capabilities:
            agents = self.registry.get_agents_by_capability(capability)
            if agents:
                best_agent = self.select_best_agent(agents, capability)
                workflow_steps.append({
                    "agent": best_agent.name,
                    "instruction": f"Handle {capability} for: {requirements}",
                    "capability": capability
                })
        
        # Execute workflow
        if workflow_steps:
            workflow_config = {
                "name": f"workflow_{int(datetime.now().timestamp())}",
                "steps": workflow_steps,
                "context": {"requirements": requirements, "state": state}
            }
            
            result = await self.orchestrator.execute_workflow(workflow_config)
            return result
        else:
            return {"error": "No suitable agents found for requirements"}
    
    def analyze_requirements(self, requirements: str) -> List[str]:
        """Analyze requirements to determine needed capabilities"""
        capabilities = []
        requirements_lower = requirements.lower()
        
        # Simple keyword-based analysis
        capability_keywords = {
            "web_search": ["search", "find", "lookup", "research"],
            "web_scraping": ["scrape", "extract", "crawl", "fetch"],
            "data_analysis": ["analyze", "process", "calculate", "statistics"],
            "content_generation": ["generate", "create", "write", "compose"],
            "summarization": ["summarize", "summary", "brief"],
            "translation": ["translate", "translation"],
            "classification": ["classify", "categorize", "label"]
        }
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in requirements_lower for keyword in keywords):
                capabilities.append(capability)
        
        return capabilities
    
    def select_best_agent(self, agents: List[MicroAgentConfig], capability: str) -> MicroAgentConfig:
        """Select the best agent for a specific capability"""
        # Simple selection based on trigger type preference
        always_agents = [a for a in agents if a.trigger_type == "always"]
        if always_agents:
            return always_agents[0]
        
        return agents[0]
    
    def invoke(self, state: StateT, requirements: str) -> Dict[str, Any]:
        """Invoke the meta agent with microservice orchestration"""
        try:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                self.orchestrate_workflow(requirements, state)
            )
            
            # Write result to state
            self.write_to_state(state, json.dumps(result))
            
        except Exception as e:
            error_result = {"error": str(e), "agent": self.name}
            self.write_to_state(state, json.dumps(error_result))
        
        return state

class MicroServiceToolCallingAgent(HybridAgent[StateT]):
    """
    Tool calling agent with microservice integration
    """
    
    def get_guided_json(self, state: StateT) -> Dict[str, Any]:
        """Get guided JSON for tool calling"""
        # Base guided JSON schema
        base_schema = {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform"
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters for the action"
                }
            },
            "required": ["action", "parameters"]
        }
        
        # Add microservice-specific properties if available
        if self.microservice_config:
            base_schema["properties"]["use_microservice"] = {
                "type": "boolean",
                "description": "Whether to use microservice for this action"
            }
            base_schema["properties"]["microservice_context"] = {
                "type": "object",
                "description": "Additional context for microservice"
            }
        
        return base_schema
    
    def execute_tool_local(self, tool_response: Dict[str, Any], state: StateT) -> StateT:
        """Execute tool locally"""
        # Default implementation - subclasses should override
        action = tool_response.get("action", "unknown")
        parameters = tool_response.get("parameters", {})
        
        result = {
            "action": action,
            "parameters": parameters,
            "result": f"Executed {action} locally with parameters: {parameters}",
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result)

# Factory functions for creating enhanced agents
def create_microservice_agent(name: str, microservice_name: str, 
                            registry: MicroServiceAgentRegistry, **kwargs) -> MicroServiceAgent:
    """Create a microservice agent"""
    config = registry.get_agent(microservice_name)
    if not config:
        raise ValueError(f"Microservice {microservice_name} not found in registry")
    
    return MicroServiceAgent(name, config, registry, **kwargs)

def create_hybrid_agent(name: str, microservice_name: Optional[str] = None,
                       registry: Optional[MicroServiceAgentRegistry] = None, 
                       **kwargs) -> HybridAgent:
    """Create a hybrid agent"""
    config = None
    if microservice_name and registry:
        config = registry.get_agent(microservice_name)
    
    return HybridAgent(name, config, registry, **kwargs)

def create_microservice_meta_agent(name: str, registry: MicroServiceAgentRegistry, 
                                 **kwargs) -> MicroServiceMetaAgent:
    """Create a microservice meta agent"""
    return MicroServiceMetaAgent(name, registry, **kwargs)