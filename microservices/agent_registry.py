"""
Enhanced Agent Registry with Microservice Support
Similar to OpenHands microagents architecture
"""
import json
import os
import yaml
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class MicroAgentConfig:
    """Configuration for a microservice agent"""
    name: str
    description: str
    prompt: str
    trigger_type: str = "always"  # always, on_demand, repository
    capabilities: List[str] = None
    dependencies: List[str] = None
    endpoint: Optional[str] = None
    container_image: Optional[str] = None
    environment_vars: Dict[str, str] = None
    resource_limits: Dict[str, Any] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.dependencies is None:
            self.dependencies = []
        if self.environment_vars is None:
            self.environment_vars = {}
        if self.resource_limits is None:
            self.resource_limits = {"memory": "512Mi", "cpu": "0.5"}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class MicroServiceAgentRegistry:
    """
    Enhanced agent registry supporting dynamic microservice agents
    """
    
    def __init__(self, microagents_dir: str = ".jar3d/microagents"):
        self.microagents_dir = Path(microagents_dir)
        self.microagents_dir.mkdir(parents=True, exist_ok=True)
        self.agents: Dict[str, MicroAgentConfig] = {}
        self.active_services: Dict[str, Dict[str, Any]] = {}
        self.load_microagents()
    
    def load_microagents(self):
        """Load microagents from the microagents directory"""
        if not self.microagents_dir.exists():
            return
        
        # Load from markdown files (OpenHands style)
        for md_file in self.microagents_dir.glob("*.md"):
            try:
                self._load_microagent_from_md(md_file)
            except Exception as e:
                logger.error(f"Error loading microagent from {md_file}: {e}")
        
        # Load from YAML configuration files
        for yaml_file in self.microagents_dir.glob("*.yaml"):
            try:
                self._load_microagent_from_yaml(yaml_file)
            except Exception as e:
                logger.error(f"Error loading microagent from {yaml_file}: {e}")
    
    def _load_microagent_from_md(self, md_file: Path):
        """Load microagent from markdown file with frontmatter"""
        content = md_file.read_text(encoding='utf-8')
        
        # Parse frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                prompt_content = parts[2].strip()
            else:
                frontmatter = {}
                prompt_content = content
        else:
            frontmatter = {}
            prompt_content = content
        
        # Create microagent config
        name = frontmatter.get('name', md_file.stem)
        config = MicroAgentConfig(
            name=name,
            description=frontmatter.get('description', f'Microagent {name}'),
            prompt=prompt_content,
            trigger_type=frontmatter.get('trigger_type', 'always'),
            capabilities=frontmatter.get('capabilities', []),
            dependencies=frontmatter.get('dependencies', []),
            endpoint=frontmatter.get('endpoint'),
            container_image=frontmatter.get('container_image'),
            environment_vars=frontmatter.get('environment_vars', {}),
            resource_limits=frontmatter.get('resource_limits', {})
        )
        
        self.agents[name] = config
        logger.info(f"Loaded microagent: {name}")
    
    def _load_microagent_from_yaml(self, yaml_file: Path):
        """Load microagent from YAML configuration file"""
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        name = data.get('name', yaml_file.stem)
        config = MicroAgentConfig(**data)
        self.agents[name] = config
        logger.info(f"Loaded microagent from YAML: {name}")
    
    def register_agent(self, config: Union[MicroAgentConfig, Dict[str, Any]]) -> bool:
        """Register a new microservice agent"""
        if isinstance(config, dict):
            config = MicroAgentConfig(**config)
        
        self.agents[config.name] = config
        
        # Save to file
        self._save_agent_config(config)
        
        logger.info(f"Registered microagent: {config.name}")
        return True
    
    def _save_agent_config(self, config: MicroAgentConfig):
        """Save agent configuration to file"""
        config_file = self.microagents_dir / f"{config.name}.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(asdict(config), f, default_flow_style=False)
    
    def unregister_agent(self, name: str) -> bool:
        """Unregister a microservice agent"""
        if name in self.agents:
            del self.agents[name]
            
            # Remove config file
            config_file = self.microagents_dir / f"{name}.yaml"
            if config_file.exists():
                config_file.unlink()
            
            # Stop service if running
            if name in self.active_services:
                self.stop_service(name)
            
            logger.info(f"Unregistered microagent: {name}")
            return True
        return False
    
    def get_agent(self, name: str) -> Optional[MicroAgentConfig]:
        """Get agent configuration by name"""
        return self.agents.get(name)
    
    def list_agents(self, trigger_type: Optional[str] = None) -> List[MicroAgentConfig]:
        """List all registered agents, optionally filtered by trigger type"""
        agents = list(self.agents.values())
        if trigger_type:
            agents = [agent for agent in agents if agent.trigger_type == trigger_type]
        return agents
    
    def create_agent_from_prompt(self, name: str, description: str, prompt: str, 
                                capabilities: List[str] = None, **kwargs) -> MicroAgentConfig:
        """Create a new microagent from a prompt"""
        config = MicroAgentConfig(
            name=name,
            description=description,
            prompt=prompt,
            capabilities=capabilities or [],
            **kwargs
        )
        
        self.register_agent(config)
        return config
    
    def start_service(self, name: str) -> bool:
        """Start a microservice agent"""
        if name not in self.agents:
            logger.error(f"Agent {name} not found")
            return False
        
        config = self.agents[name]
        
        if config.endpoint:
            # External service - just check if it's running
            try:
                response = requests.get(f"{config.endpoint}/health", timeout=5)
                if response.status_code == 200:
                    self.active_services[name] = {
                        "status": "running",
                        "endpoint": config.endpoint,
                        "started_at": datetime.now().isoformat()
                    }
                    return True
            except requests.RequestException:
                logger.error(f"Failed to connect to external service: {config.endpoint}")
                return False
        
        # For containerized services, this would start the container
        # For now, we'll simulate it
        self.active_services[name] = {
            "status": "running",
            "endpoint": f"http://localhost:800{len(self.active_services) + 1}",
            "started_at": datetime.now().isoformat()
        }
        
        logger.info(f"Started microservice: {name}")
        return True
    
    def stop_service(self, name: str) -> bool:
        """Stop a microservice agent"""
        if name in self.active_services:
            del self.active_services[name]
            logger.info(f"Stopped microservice: {name}")
            return True
        return False
    
    def get_service_status(self, name: str) -> Optional[Dict[str, Any]]:
        """Get the status of a microservice"""
        return self.active_services.get(name)
    
    def list_active_services(self) -> Dict[str, Dict[str, Any]]:
        """List all active microservices"""
        return self.active_services.copy()
    
    def get_agents_by_capability(self, capability: str) -> List[MicroAgentConfig]:
        """Get agents that have a specific capability"""
        return [agent for agent in self.agents.values() 
                if capability in agent.capabilities]
    
    def export_registry(self) -> Dict[str, Any]:
        """Export the entire registry to a dictionary"""
        return {
            "agents": {name: asdict(config) for name, config in self.agents.items()},
            "active_services": self.active_services
        }
    
    def import_registry(self, data: Dict[str, Any]):
        """Import registry from a dictionary"""
        if "agents" in data:
            for name, agent_data in data["agents"].items():
                config = MicroAgentConfig(**agent_data)
                self.agents[name] = config
        
        if "active_services" in data:
            self.active_services.update(data["active_services"])

# Global registry instance
microservice_registry = MicroServiceAgentRegistry()