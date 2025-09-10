"""
Microservice Agent Architecture for Jar3d
Similar to OpenHands microagents with dynamic provisioning
"""

from .agent_registry import MicroServiceAgentRegistry, MicroAgentConfig, microservice_registry
from .orchestrator import MicroServiceOrchestrator, get_orchestrator
from .microagent_framework import MicroAgentFactory, MicroAgentTemplate
from .enhanced_agent_base import (
    MicroServiceAgent, HybridAgent, MicroServiceMetaAgent,
    create_microservice_agent, create_hybrid_agent, create_microservice_meta_agent
)
from .integration import MicroServiceIntegration, get_microservice_integration, initialize_microservices

__all__ = [
    # Registry
    'MicroServiceAgentRegistry',
    'MicroAgentConfig', 
    'microservice_registry',
    
    # Orchestration
    'MicroServiceOrchestrator',
    'get_orchestrator',
    
    # Framework
    'MicroAgentFactory',
    'MicroAgentTemplate',
    
    # Enhanced Agents
    'MicroServiceAgent',
    'HybridAgent', 
    'MicroServiceMetaAgent',
    'create_microservice_agent',
    'create_hybrid_agent',
    'create_microservice_meta_agent',
    
    # Integration
    'MicroServiceIntegration',
    'get_microservice_integration',
    'initialize_microservices'
]