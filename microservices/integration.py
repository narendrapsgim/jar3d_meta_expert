"""
Integration layer for connecting microservice architecture with existing Jar3d system
"""
import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .agent_registry import MicroServiceAgentRegistry, microservice_registry
from .microagent_framework import MicroAgentFactory, initialize_default_templates
from .orchestrator import get_orchestrator
from .enhanced_agent_base import (
    MicroServiceAgent, HybridAgent, MicroServiceMetaAgent,
    create_microservice_agent, create_hybrid_agent, create_microservice_meta_agent
)

logger = logging.getLogger(__name__)

class MicroServiceIntegration:
    """
    Integration layer for microservice architecture
    """
    
    def __init__(self, microagents_dir: str = ".jar3d/microagents"):
        self.registry = microservice_registry
        self.factory = MicroAgentFactory(self.registry, microagents_dir)
        self.orchestrator = get_orchestrator(self.registry)
        self.microagents_dir = Path(microagents_dir)
        self.microagents_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize with default templates
        initialize_default_templates(self.factory)
        
        # Auto-discover and register microagents
        self.discover_microagents()
    
    def discover_microagents(self):
        """Discover and register microagents from the microagents directory"""
        try:
            # Load existing microagents
            self.registry.load_microagents()
            
            # Register default microservices if they don't exist
            self.register_default_microservices()
            
            logger.info(f"Discovered {len(self.registry.agents)} microagents")
            
        except Exception as e:
            logger.error(f"Error discovering microagents: {e}")
    
    def register_default_microservices(self):
        """Register default microservices"""
        default_services = [
            {
                "name": "web_search_agent",
                "description": "Web search and information retrieval agent",
                "prompt": "You are a web search specialist. Perform comprehensive web searches and return relevant results.",
                "capabilities": ["web_search", "information_retrieval"],
                "endpoint": "http://web-search-service:8000",
                "trigger_type": "always"
            },
            {
                "name": "content_generator_agent", 
                "description": "Content generation and writing agent",
                "prompt": "You are a content creation specialist. Generate high-quality written content for various purposes.",
                "capabilities": ["content_generation", "writing", "summarization"],
                "endpoint": "http://content-generator-service:8000",
                "trigger_type": "always"
            },
            {
                "name": "data_analysis_agent",
                "description": "Data analysis and processing agent", 
                "prompt": "You are a data analysis specialist. Process, analyze, and derive insights from various types of data.",
                "capabilities": ["data_analysis", "statistics", "visualization"],
                "endpoint": "http://data-analysis-service:8000",
                "trigger_type": "always"
            }
        ]
        
        for service_config in default_services:
            if not self.registry.get_agent(service_config["name"]):
                self.registry.register_agent(service_config)
                logger.info(f"Registered default microservice: {service_config['name']}")
    
    def create_microagent_from_prompt(self, name: str, prompt: str, **kwargs) -> str:
        """Create a microagent from a prompt and return its name"""
        try:
            config = self.factory.create_agent_from_prompt(
                name=name,
                user_prompt=prompt,
                additional_config=kwargs
            )
            
            # Start the service if it has an endpoint
            if config.endpoint:
                self.registry.start_service(name)
            
            logger.info(f"Created microagent from prompt: {name}")
            return name
            
        except Exception as e:
            logger.error(f"Error creating microagent from prompt: {e}")
            raise
    
    def get_enhanced_agents_for_workflow(self, agent_team: List[Any]) -> List[Any]:
        """Convert existing agents to enhanced agents with microservice support"""
        enhanced_agents = []
        
        for agent in agent_team:
            agent_name = agent.name
            
            # Check if there's a corresponding microservice
            microservice_config = self.registry.get_agent(agent_name)
            
            if microservice_config:
                # Create hybrid agent that can use both local and microservice execution
                enhanced_agent = create_hybrid_agent(
                    name=agent_name,
                    microservice_name=agent_name,
                    registry=self.registry,
                    model=getattr(agent, 'model', None),
                    server=getattr(agent, 'server', None),
                    temperature=getattr(agent, 'temperature', 0)
                )
                enhanced_agents.append(enhanced_agent)
            else:
                # Keep original agent
                enhanced_agents.append(agent)
        
        return enhanced_agents
    
    def create_microservice_meta_agent(self, name: str = "microservice_meta_agent", **kwargs):
        """Create a meta agent that can orchestrate microservices"""
        return create_microservice_meta_agent(
            name=name,
            registry=self.registry,
            **kwargs
        )
    
    async def execute_microservice_workflow(self, requirements: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a workflow using microservices"""
        try:
            # Create workflow configuration
            workflow_config = {
                "name": f"microservice_workflow_{int(asyncio.get_event_loop().time())}",
                "steps": self.analyze_requirements_to_steps(requirements),
                "context": context or {}
            }
            
            # Execute workflow
            result = await self.orchestrator.execute_workflow(workflow_config)
            return result
            
        except Exception as e:
            logger.error(f"Error executing microservice workflow: {e}")
            return {"error": str(e)}
    
    def analyze_requirements_to_steps(self, requirements: str) -> List[Dict[str, Any]]:
        """Analyze requirements and convert to workflow steps"""
        steps = []
        requirements_lower = requirements.lower()
        
        # Simple analysis - in a real implementation, this would be more sophisticated
        if any(keyword in requirements_lower for keyword in ["search", "find", "lookup"]):
            steps.append({
                "agent": "web_search_agent",
                "instruction": f"Search for information about: {requirements}",
                "timeout": 60
            })
        
        if any(keyword in requirements_lower for keyword in ["analyze", "process", "calculate"]):
            steps.append({
                "agent": "data_analysis_agent", 
                "instruction": f"Analyze data related to: {requirements}",
                "depends_on": ["web_search_agent"] if steps else [],
                "timeout": 120
            })
        
        if any(keyword in requirements_lower for keyword in ["generate", "create", "write"]):
            steps.append({
                "agent": "content_generator_agent",
                "instruction": f"Generate content for: {requirements}",
                "depends_on": [step["agent"] for step in steps] if steps else [],
                "timeout": 90
            })
        
        # If no specific steps identified, use a general approach
        if not steps:
            steps = [
                {
                    "agent": "web_search_agent",
                    "instruction": f"Research: {requirements}",
                    "timeout": 60
                },
                {
                    "agent": "content_generator_agent", 
                    "instruction": f"Provide a comprehensive response for: {requirements}",
                    "depends_on": ["web_search_agent"],
                    "timeout": 90
                }
            ]
        
        return steps
    
    def get_microservice_status(self) -> Dict[str, Any]:
        """Get status of all microservices"""
        return {
            "registry": {
                "total_agents": len(self.registry.agents),
                "active_services": len(self.registry.active_services),
                "agents": list(self.registry.agents.keys())
            },
            "orchestrator": {
                "active_tasks": len(self.orchestrator.active_tasks),
                "completed_tasks": len(self.orchestrator.task_results)
            },
            "services": self.registry.list_active_services()
        }
    
    def start_all_services(self) -> Dict[str, bool]:
        """Start all registered microservices"""
        results = {}
        
        for agent_name in self.registry.agents.keys():
            try:
                success = self.registry.start_service(agent_name)
                results[agent_name] = success
            except Exception as e:
                logger.error(f"Error starting service {agent_name}: {e}")
                results[agent_name] = False
        
        return results
    
    def stop_all_services(self) -> Dict[str, bool]:
        """Stop all active microservices"""
        results = {}
        
        for agent_name in list(self.registry.active_services.keys()):
            try:
                success = self.registry.stop_service(agent_name)
                results[agent_name] = success
            except Exception as e:
                logger.error(f"Error stopping service {agent_name}: {e}")
                results[agent_name] = False
        
        return results
    
    def export_configuration(self, file_path: str):
        """Export microservice configuration to file"""
        config = {
            "registry": self.registry.export_registry(),
            "templates": [
                {
                    "name": template.name,
                    "description": template.description,
                    "capabilities": template.capabilities,
                    "required_tools": template.required_tools
                }
                for template in self.factory.list_templates()
            ]
        }
        
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration exported to: {file_path}")
    
    def import_configuration(self, file_path: str):
        """Import microservice configuration from file"""
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        if "registry" in config:
            self.registry.import_registry(config["registry"])
        
        logger.info(f"Configuration imported from: {file_path}")

# Global integration instance
_integration_instance = None

def get_microservice_integration(microagents_dir: str = ".jar3d/microagents") -> MicroServiceIntegration:
    """Get or create the global microservice integration instance"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = MicroServiceIntegration(microagents_dir)
    return _integration_instance

def initialize_microservices():
    """Initialize microservice integration"""
    integration = get_microservice_integration()
    integration.orchestrator.start()
    logger.info("Microservice integration initialized")
    return integration