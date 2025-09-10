#!/usr/bin/env python3
"""
Microagent Management CLI
Command-line interface for managing microservice agents
"""
import argparse
import json
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any

from .agent_registry import MicroServiceAgentRegistry, MicroAgentConfig
from .microagent_framework import MicroAgentFactory, initialize_default_templates
from .orchestrator import get_orchestrator
from .api_gateway import gateway

def create_agent_command(args):
    """Create a new microagent"""
    registry = MicroServiceAgentRegistry()
    factory = MicroAgentFactory(registry)
    
    try:
        if args.template:
            # Create from template
            config = factory.create_agent_from_template(
                name=args.name,
                template_name=args.template,
                customizations=json.loads(args.customizations) if args.customizations else None
            )
        else:
            # Create from prompt
            config = factory.create_agent_from_prompt(
                name=args.name,
                user_prompt=args.prompt,
                additional_config=json.loads(args.config) if args.config else None
            )
        
        print(f"✅ Created microagent: {config.name}")
        print(f"   Description: {config.description}")
        print(f"   Capabilities: {', '.join(config.capabilities)}")
        
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        sys.exit(1)

def list_agents_command(args):
    """List all registered agents"""
    registry = MicroServiceAgentRegistry()
    agents = registry.list_agents(trigger_type=args.trigger_type)
    
    if not agents:
        print("No agents found.")
        return
    
    print(f"Found {len(agents)} agent(s):")
    print()
    
    for agent in agents:
        print(f"🤖 {agent.name}")
        print(f"   Description: {agent.description}")
        print(f"   Trigger: {agent.trigger_type}")
        print(f"   Capabilities: {', '.join(agent.capabilities)}")
        if agent.dependencies:
            print(f"   Dependencies: {', '.join(agent.dependencies)}")
        print()

def delete_agent_command(args):
    """Delete an agent"""
    registry = MicroServiceAgentRegistry()
    
    if registry.unregister_agent(args.name):
        print(f"✅ Deleted agent: {args.name}")
    else:
        print(f"❌ Agent not found: {args.name}")
        sys.exit(1)

def start_service_command(args):
    """Start a microservice"""
    registry = MicroServiceAgentRegistry()
    
    if registry.start_service(args.name):
        print(f"✅ Started service: {args.name}")
    else:
        print(f"❌ Failed to start service: {args.name}")
        sys.exit(1)

def stop_service_command(args):
    """Stop a microservice"""
    registry = MicroServiceAgentRegistry()
    
    if registry.stop_service(args.name):
        print(f"✅ Stopped service: {args.name}")
    else:
        print(f"❌ Service not found: {args.name}")
        sys.exit(1)

def list_services_command(args):
    """List active services"""
    registry = MicroServiceAgentRegistry()
    services = registry.list_active_services()
    
    if not services:
        print("No active services.")
        return
    
    print(f"Found {len(services)} active service(s):")
    print()
    
    for name, info in services.items():
        print(f"🚀 {name}")
        print(f"   Status: {info.get('status', 'unknown')}")
        print(f"   Endpoint: {info.get('endpoint', 'N/A')}")
        print(f"   Started: {info.get('started_at', 'N/A')}")
        print()

async def submit_task_command(args):
    """Submit a task to an agent"""
    registry = MicroServiceAgentRegistry()
    orchestrator = get_orchestrator(registry)
    
    try:
        task_id = await orchestrator.submit_task(
            agent_name=args.agent,
            instruction=args.instruction,
            context=json.loads(args.context) if args.context else {},
            timeout=args.timeout
        )
        
        print(f"✅ Submitted task: {task_id}")
        
        if args.wait:
            print("⏳ Waiting for result...")
            result = await orchestrator.wait_for_task(task_id, timeout=args.timeout)
            
            if result.status == "success":
                print(f"✅ Task completed successfully:")
                print(json.dumps(result.result, indent=2))
            else:
                print(f"❌ Task failed: {result.error}")
                sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error submitting task: {e}")
        sys.exit(1)

async def get_task_status_command(args):
    """Get task status"""
    registry = MicroServiceAgentRegistry()
    orchestrator = get_orchestrator(registry)
    
    status = orchestrator.get_task_status(args.task_id)
    if status:
        print(f"Task {args.task_id}:")
        print(json.dumps(status, indent=2))
    else:
        print(f"❌ Task not found: {args.task_id}")
        sys.exit(1)

def list_templates_command(args):
    """List available templates"""
    registry = MicroServiceAgentRegistry()
    factory = MicroAgentFactory(registry)
    initialize_default_templates(factory)
    
    templates = factory.list_templates()
    
    if not templates:
        print("No templates found.")
        return
    
    print(f"Found {len(templates)} template(s):")
    print()
    
    for template in templates:
        print(f"📋 {template.name}")
        print(f"   Description: {template.description}")
        print(f"   Capabilities: {', '.join(template.capabilities)}")
        if template.required_tools:
            print(f"   Required Tools: {', '.join(template.required_tools)}")
        print()

def export_registry_command(args):
    """Export registry to file"""
    registry = MicroServiceAgentRegistry()
    data = registry.export_registry()
    
    with open(args.file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Registry exported to: {args.file}")

def import_registry_command(args):
    """Import registry from file"""
    registry = MicroServiceAgentRegistry()
    
    try:
        with open(args.file, 'r') as f:
            data = json.load(f)
        
        registry.import_registry(data)
        print(f"✅ Registry imported from: {args.file}")
        
    except Exception as e:
        print(f"❌ Error importing registry: {e}")
        sys.exit(1)

def start_gateway_command(args):
    """Start the API gateway"""
    print("🚀 Starting API Gateway...")
    gateway.run(host=args.host, port=args.port)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Microagent Management CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create agent command
    create_parser = subparsers.add_parser('create', help='Create a new microagent')
    create_parser.add_argument('name', help='Agent name')
    create_parser.add_argument('--prompt', help='Agent prompt/description')
    create_parser.add_argument('--template', help='Template name to use')
    create_parser.add_argument('--config', help='Additional configuration (JSON)')
    create_parser.add_argument('--customizations', help='Template customizations (JSON)')
    create_parser.set_defaults(func=create_agent_command)
    
    # List agents command
    list_parser = subparsers.add_parser('list', help='List registered agents')
    list_parser.add_argument('--trigger-type', help='Filter by trigger type')
    list_parser.set_defaults(func=list_agents_command)
    
    # Delete agent command
    delete_parser = subparsers.add_parser('delete', help='Delete an agent')
    delete_parser.add_argument('name', help='Agent name')
    delete_parser.set_defaults(func=delete_agent_command)
    
    # Start service command
    start_parser = subparsers.add_parser('start', help='Start a microservice')
    start_parser.add_argument('name', help='Service name')
    start_parser.set_defaults(func=start_service_command)
    
    # Stop service command
    stop_parser = subparsers.add_parser('stop', help='Stop a microservice')
    stop_parser.add_argument('name', help='Service name')
    stop_parser.set_defaults(func=stop_service_command)
    
    # List services command
    services_parser = subparsers.add_parser('services', help='List active services')
    services_parser.set_defaults(func=list_services_command)
    
    # Submit task command
    task_parser = subparsers.add_parser('task', help='Submit a task to an agent')
    task_parser.add_argument('agent', help='Agent name')
    task_parser.add_argument('instruction', help='Task instruction')
    task_parser.add_argument('--context', help='Task context (JSON)')
    task_parser.add_argument('--timeout', type=int, default=300, help='Task timeout')
    task_parser.add_argument('--wait', action='store_true', help='Wait for result')
    task_parser.set_defaults(func=lambda args: asyncio.run(submit_task_command(args)))
    
    # Get task status command
    status_parser = subparsers.add_parser('status', help='Get task status')
    status_parser.add_argument('task_id', help='Task ID')
    status_parser.set_defaults(func=lambda args: asyncio.run(get_task_status_command(args)))
    
    # List templates command
    templates_parser = subparsers.add_parser('templates', help='List available templates')
    templates_parser.set_defaults(func=list_templates_command)
    
    # Export registry command
    export_parser = subparsers.add_parser('export', help='Export registry to file')
    export_parser.add_argument('file', help='Output file path')
    export_parser.set_defaults(func=export_registry_command)
    
    # Import registry command
    import_parser = subparsers.add_parser('import', help='Import registry from file')
    import_parser.add_argument('file', help='Input file path')
    import_parser.set_defaults(func=import_registry_command)
    
    # Start gateway command
    gateway_parser = subparsers.add_parser('gateway', help='Start API gateway')
    gateway_parser.add_argument('--host', default='0.0.0.0', help='Gateway host')
    gateway_parser.add_argument('--port', type=int, default=8000, help='Gateway port')
    gateway_parser.set_defaults(func=start_gateway_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    args.func(args)

if __name__ == '__main__':
    main()