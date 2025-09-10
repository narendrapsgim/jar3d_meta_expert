"""
Microagent Framework with Prompt-based Provisioning
Allows dynamic creation of agents through prompts and configuration
"""
import os
import json
import yaml
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import re

from .agent_registry import MicroServiceAgentRegistry, MicroAgentConfig
from agents.agent_base import BaseAgent, ToolCallingAgent

logger = logging.getLogger(__name__)

@dataclass
class MicroAgentTemplate:
    """Template for creating microagents"""
    name: str
    description: str
    base_prompt: str
    capabilities: List[str]
    required_tools: List[str] = None
    optional_tools: List[str] = None
    environment_setup: Dict[str, Any] = None
    resource_requirements: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.required_tools is None:
            self.required_tools = []
        if self.optional_tools is None:
            self.optional_tools = []
        if self.environment_setup is None:
            self.environment_setup = {}
        if self.resource_requirements is None:
            self.resource_requirements = {"memory": "256Mi", "cpu": "0.25"}

class MicroAgentFactory:
    """Factory for creating microagents from prompts and templates"""
    
    def __init__(self, registry: MicroServiceAgentRegistry, templates_dir: str = ".jar3d/templates"):
        self.registry = registry
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates: Dict[str, MicroAgentTemplate] = {}
        self.load_templates()
    
    def load_templates(self):
        """Load microagent templates from the templates directory"""
        if not self.templates_dir.exists():
            return
        
        for template_file in self.templates_dir.glob("*.yaml"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                template = MicroAgentTemplate(**data)
                self.templates[template.name] = template
                logger.info(f"Loaded template: {template.name}")
                
            except Exception as e:
                logger.error(f"Error loading template from {template_file}: {e}")
    
    def create_template(self, template: MicroAgentTemplate) -> bool:
        """Create and save a new template"""
        try:
            self.templates[template.name] = template
            
            # Save to file
            template_file = self.templates_dir / f"{template.name}.yaml"
            with open(template_file, 'w', encoding='utf-8') as f:
                yaml.dump(asdict(template), f, default_flow_style=False)
            
            logger.info(f"Created template: {template.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return False
    
    def get_template(self, name: str) -> Optional[MicroAgentTemplate]:
        """Get a template by name"""
        return self.templates.get(name)
    
    def list_templates(self) -> List[MicroAgentTemplate]:
        """List all available templates"""
        return list(self.templates.values())
    
    def create_agent_from_prompt(self, name: str, user_prompt: str, 
                                template_name: Optional[str] = None,
                                additional_config: Dict[str, Any] = None) -> MicroAgentConfig:
        """Create a microagent from a user prompt"""
        
        # Get template if specified
        template = None
        if template_name:
            template = self.get_template(template_name)
            if not template:
                raise ValueError(f"Template {template_name} not found")
        
        # Parse the user prompt to extract agent requirements
        agent_spec = self._parse_user_prompt(user_prompt, template)
        
        # Apply additional configuration
        if additional_config:
            agent_spec.update(additional_config)
        
        # Create the microagent configuration
        config = MicroAgentConfig(
            name=name,
            description=agent_spec.get("description", f"Agent created from prompt: {user_prompt[:100]}..."),
            prompt=self._build_agent_prompt(user_prompt, template, agent_spec),
            trigger_type=agent_spec.get("trigger_type", "always"),
            capabilities=agent_spec.get("capabilities", []),
            dependencies=agent_spec.get("dependencies", []),
            environment_vars=agent_spec.get("environment_vars", {}),
            resource_limits=agent_spec.get("resource_limits", {"memory": "512Mi", "cpu": "0.5"})
        )
        
        # Register the agent
        self.registry.register_agent(config)
        
        logger.info(f"Created microagent from prompt: {name}")
        return config
    
    def _parse_user_prompt(self, user_prompt: str, template: Optional[MicroAgentTemplate] = None) -> Dict[str, Any]:
        """Parse user prompt to extract agent requirements"""
        agent_spec = {}
        
        # Extract capabilities from prompt
        capabilities = []
        
        # Common capability patterns
        capability_patterns = {
            r'\b(search|searching|find|lookup)\b': 'web_search',
            r'\b(scrape|scraping|extract|crawl)\b': 'web_scraping',
            r'\b(analyze|analysis|process|processing)\b': 'data_analysis',
            r'\b(generate|create|write|writing)\b': 'content_generation',
            r'\b(translate|translation)\b': 'translation',
            r'\b(summarize|summary|summarization)\b': 'summarization',
            r'\b(classify|classification|categorize)\b': 'classification',
            r'\b(monitor|monitoring|watch|tracking)\b': 'monitoring',
            r'\b(api|apis|integration|integrate)\b': 'api_integration',
            r'\b(database|db|sql|query)\b': 'database_access',
            r'\b(file|files|document|documents)\b': 'file_processing',
            r'\b(email|mail|notification|notify)\b': 'communication',
            r'\b(schedule|scheduling|cron|timer)\b': 'scheduling',
            r'\b(security|secure|encrypt|decrypt)\b': 'security',
            r'\b(image|images|vision|visual)\b': 'image_processing',
            r'\b(audio|sound|speech|voice)\b': 'audio_processing'
        }
        
        prompt_lower = user_prompt.lower()
        for pattern, capability in capability_patterns.items():
            if re.search(pattern, prompt_lower):
                capabilities.append(capability)
        
        agent_spec['capabilities'] = capabilities
        
        # Extract trigger type
        if re.search(r'\b(always|continuous|persistent)\b', prompt_lower):
            agent_spec['trigger_type'] = 'always'
        elif re.search(r'\b(on.demand|manual|when.needed)\b', prompt_lower):
            agent_spec['trigger_type'] = 'on_demand'
        elif re.search(r'\b(repository|repo|project)\b', prompt_lower):
            agent_spec['trigger_type'] = 'repository'
        else:
            agent_spec['trigger_type'] = 'always'
        
        # Extract dependencies
        dependencies = []
        if 'database' in prompt_lower:
            dependencies.append('database')
        if 'redis' in prompt_lower:
            dependencies.append('redis')
        if 'elasticsearch' in prompt_lower:
            dependencies.append('elasticsearch')
        
        agent_spec['dependencies'] = dependencies
        
        # Extract resource requirements
        resource_limits = {"memory": "512Mi", "cpu": "0.5"}
        
        if re.search(r'\b(heavy|intensive|large|big)\b', prompt_lower):
            resource_limits = {"memory": "1Gi", "cpu": "1.0"}
        elif re.search(r'\b(light|simple|small|minimal)\b', prompt_lower):
            resource_limits = {"memory": "256Mi", "cpu": "0.25"}
        
        agent_spec['resource_limits'] = resource_limits
        
        # Use template defaults if available
        if template:
            agent_spec.setdefault('capabilities', []).extend(template.capabilities)
            agent_spec.setdefault('dependencies', []).extend(template.required_tools)
            agent_spec.setdefault('resource_limits', {}).update(template.resource_requirements)
        
        return agent_spec
    
    def _build_agent_prompt(self, user_prompt: str, template: Optional[MicroAgentTemplate], 
                           agent_spec: Dict[str, Any]) -> str:
        """Build the complete agent prompt"""
        
        prompt_parts = []
        
        # Add template base prompt if available
        if template:
            prompt_parts.append(f"# Base Instructions\n{template.base_prompt}")
        
        # Add user-specific instructions
        prompt_parts.append(f"# User Requirements\n{user_prompt}")
        
        # Add capability-specific instructions
        capabilities = agent_spec.get('capabilities', [])
        if capabilities:
            capability_instructions = self._get_capability_instructions(capabilities)
            if capability_instructions:
                prompt_parts.append(f"# Capability Instructions\n{capability_instructions}")
        
        # Add operational guidelines
        guidelines = self._get_operational_guidelines(agent_spec)
        if guidelines:
            prompt_parts.append(f"# Operational Guidelines\n{guidelines}")
        
        return "\n\n".join(prompt_parts)
    
    def _get_capability_instructions(self, capabilities: List[str]) -> str:
        """Get instructions for specific capabilities"""
        instructions = []
        
        capability_instructions = {
            'web_search': "When performing web searches, use reliable search engines and verify information from multiple sources.",
            'web_scraping': "When scraping web content, respect robots.txt files and rate limits. Extract only relevant information.",
            'data_analysis': "When analyzing data, provide clear insights and visualizations where appropriate.",
            'content_generation': "When generating content, ensure it's relevant, accurate, and well-structured.",
            'translation': "When translating text, maintain context and cultural nuances.",
            'summarization': "When summarizing content, capture key points while maintaining accuracy.",
            'classification': "When classifying data, use consistent criteria and provide confidence scores.",
            'monitoring': "When monitoring systems, set appropriate thresholds and alert mechanisms.",
            'api_integration': "When integrating with APIs, handle errors gracefully and respect rate limits.",
            'database_access': "When accessing databases, use parameterized queries and follow security best practices.",
            'file_processing': "When processing files, handle different formats and validate input data.",
            'communication': "When sending communications, ensure messages are clear and appropriate.",
            'scheduling': "When scheduling tasks, consider time zones and dependencies.",
            'security': "When handling security operations, follow principle of least privilege.",
            'image_processing': "When processing images, maintain quality and handle different formats.",
            'audio_processing': "When processing audio, preserve quality and handle various codecs."
        }
        
        for capability in capabilities:
            if capability in capability_instructions:
                instructions.append(f"- {capability_instructions[capability]}")
        
        return "\n".join(instructions)
    
    def _get_operational_guidelines(self, agent_spec: Dict[str, Any]) -> str:
        """Get operational guidelines based on agent specification"""
        guidelines = []
        
        # Add resource-aware guidelines
        resource_limits = agent_spec.get('resource_limits', {})
        memory_limit = resource_limits.get('memory', '512Mi')
        
        if 'Gi' in memory_limit:
            guidelines.append("- You have high memory resources available for complex operations.")
        else:
            guidelines.append("- Be mindful of memory usage and optimize for efficiency.")
        
        # Add dependency guidelines
        dependencies = agent_spec.get('dependencies', [])
        if dependencies:
            guidelines.append(f"- You have access to the following dependencies: {', '.join(dependencies)}")
        
        # Add trigger-specific guidelines
        trigger_type = agent_spec.get('trigger_type', 'always')
        if trigger_type == 'always':
            guidelines.append("- You are always active and should monitor for relevant tasks continuously.")
        elif trigger_type == 'on_demand':
            guidelines.append("- You are activated on-demand and should respond promptly when called.")
        elif trigger_type == 'repository':
            guidelines.append("- You are repository-specific and should focus on project-related tasks.")
        
        return "\n".join(guidelines)
    
    def create_agent_from_template(self, name: str, template_name: str, 
                                  customizations: Dict[str, Any] = None) -> MicroAgentConfig:
        """Create a microagent from a template"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template {template_name} not found")
        
        # Apply customizations
        config_data = {
            "name": name,
            "description": template.description,
            "prompt": template.base_prompt,
            "capabilities": template.capabilities.copy(),
            "dependencies": template.required_tools.copy(),
            "resource_limits": template.resource_requirements.copy()
        }
        
        if customizations:
            config_data.update(customizations)
        
        config = MicroAgentConfig(**config_data)
        self.registry.register_agent(config)
        
        logger.info(f"Created microagent from template: {name}")
        return config
    
    def update_agent_from_prompt(self, name: str, update_prompt: str) -> bool:
        """Update an existing agent based on a new prompt"""
        existing_config = self.registry.get_agent(name)
        if not existing_config:
            raise ValueError(f"Agent {name} not found")
        
        # Parse the update prompt
        updates = self._parse_update_prompt(update_prompt)
        
        # Apply updates to the existing configuration
        updated_config = MicroAgentConfig(
            name=existing_config.name,
            description=updates.get('description', existing_config.description),
            prompt=updates.get('prompt', existing_config.prompt),
            trigger_type=updates.get('trigger_type', existing_config.trigger_type),
            capabilities=updates.get('capabilities', existing_config.capabilities),
            dependencies=updates.get('dependencies', existing_config.dependencies),
            endpoint=existing_config.endpoint,
            container_image=existing_config.container_image,
            environment_vars=updates.get('environment_vars', existing_config.environment_vars),
            resource_limits=updates.get('resource_limits', existing_config.resource_limits),
            created_at=existing_config.created_at
        )
        
        # Re-register the updated agent
        self.registry.register_agent(updated_config)
        
        logger.info(f"Updated microagent: {name}")
        return True
    
    def _parse_update_prompt(self, update_prompt: str) -> Dict[str, Any]:
        """Parse an update prompt to extract changes"""
        updates = {}
        
        # Simple parsing for demonstration
        # In a real implementation, this would be more sophisticated
        
        if "add capability" in update_prompt.lower():
            # Extract capabilities to add
            pass
        
        if "remove capability" in update_prompt.lower():
            # Extract capabilities to remove
            pass
        
        if "change description" in update_prompt.lower():
            # Extract new description
            pass
        
        return updates
    
    def clone_agent(self, source_name: str, target_name: str, 
                   modifications: Dict[str, Any] = None) -> MicroAgentConfig:
        """Clone an existing agent with optional modifications"""
        source_config = self.registry.get_agent(source_name)
        if not source_config:
            raise ValueError(f"Source agent {source_name} not found")
        
        # Create a copy of the source configuration
        clone_data = {
            "name": target_name,
            "description": source_config.description,
            "prompt": source_config.prompt,
            "trigger_type": source_config.trigger_type,
            "capabilities": source_config.capabilities.copy(),
            "dependencies": source_config.dependencies.copy(),
            "environment_vars": source_config.environment_vars.copy(),
            "resource_limits": source_config.resource_limits.copy()
        }
        
        # Apply modifications
        if modifications:
            clone_data.update(modifications)
        
        clone_config = MicroAgentConfig(**clone_data)
        self.registry.register_agent(clone_config)
        
        logger.info(f"Cloned microagent {source_name} to {target_name}")
        return clone_config

# Default templates
DEFAULT_TEMPLATES = [
    MicroAgentTemplate(
        name="web_researcher",
        description="Web research and information gathering agent",
        base_prompt="""You are a web research specialist. Your primary function is to search for, gather, and analyze information from web sources.

Key responsibilities:
- Perform comprehensive web searches on given topics
- Evaluate source credibility and reliability
- Extract and summarize relevant information
- Provide citations and references
- Cross-reference information from multiple sources

Always provide accurate, well-sourced information and clearly indicate when information cannot be verified.""",
        capabilities=["web_search", "data_analysis", "summarization"],
        required_tools=["web_search", "content_extraction"],
        resource_requirements={"memory": "512Mi", "cpu": "0.5"}
    ),
    
    MicroAgentTemplate(
        name="content_creator",
        description="Content generation and writing agent",
        base_prompt="""You are a content creation specialist. Your primary function is to generate high-quality written content for various purposes.

Key responsibilities:
- Create engaging and informative content
- Adapt writing style to target audience
- Ensure content is well-structured and coherent
- Incorporate SEO best practices when applicable
- Maintain consistency in tone and voice

Always produce original, relevant content that meets the specified requirements and quality standards.""",
        capabilities=["content_generation", "summarization", "classification"],
        required_tools=["text_generation", "grammar_check"],
        resource_requirements={"memory": "768Mi", "cpu": "0.75"}
    ),
    
    MicroAgentTemplate(
        name="data_analyst",
        description="Data analysis and processing agent",
        base_prompt="""You are a data analysis specialist. Your primary function is to process, analyze, and derive insights from various types of data.

Key responsibilities:
- Clean and preprocess data
- Perform statistical analysis
- Create visualizations and reports
- Identify patterns and trends
- Provide actionable insights

Always ensure data accuracy and provide clear, understandable analysis results.""",
        capabilities=["data_analysis", "file_processing", "classification"],
        required_tools=["data_processing", "visualization"],
        resource_requirements={"memory": "1Gi", "cpu": "1.0"}
    )
]

def initialize_default_templates(factory: MicroAgentFactory):
    """Initialize the factory with default templates"""
    for template in DEFAULT_TEMPLATES:
        factory.create_template(template)