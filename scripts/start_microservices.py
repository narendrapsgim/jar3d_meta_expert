#!/usr/bin/env python3
"""
Startup script for Jar3d microservice environment
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from microservices.integration import initialize_microservices, get_microservice_integration
from microservices.api_gateway import gateway

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main startup function"""
    print("🚀 Starting Jar3d Microservice Environment")
    print("=" * 50)
    
    try:
        # Initialize microservice integration
        print("📋 Initializing microservice integration...")
        integration = initialize_microservices()
        
        # Display status
        status = integration.get_microservice_status()
        print(f"✅ Registry initialized with {status['registry']['total_agents']} agents")
        
        # List discovered agents
        print("\n🤖 Discovered Microagents:")
        for agent_name in status['registry']['agents']:
            agent_config = integration.registry.get_agent(agent_name)
            if agent_config:
                print(f"  • {agent_name}: {agent_config.description}")
                print(f"    Capabilities: {', '.join(agent_config.capabilities)}")
        
        # Start services
        print("\n🔄 Starting microservices...")
        start_results = integration.start_all_services()
        
        for service_name, success in start_results.items():
            status_icon = "✅" if success else "❌"
            print(f"  {status_icon} {service_name}")
        
        # Display active services
        active_services = integration.registry.list_active_services()
        if active_services:
            print(f"\n🚀 Active Services ({len(active_services)}):")
            for name, info in active_services.items():
                endpoint = info.get('endpoint', 'N/A')
                print(f"  • {name}: {endpoint}")
        
        print("\n" + "=" * 50)
        print("✅ Microservice environment ready!")
        print("\nAvailable endpoints:")
        print("  • API Gateway: http://localhost:8000")
        print("  • Health Check: http://localhost:8000/health")
        print("  • Agent Management: http://localhost:8000/agents")
        print("  • Task Submission: http://localhost:8000/tasks")
        
        print("\nTo manage microagents, use:")
        print("  python -m microservices.cli --help")
        
        # Start API Gateway
        print("\n🌐 Starting API Gateway...")
        gateway.run(host="0.0.0.0", port=8000)
        
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down microservice environment...")
        
        # Stop all services
        if 'integration' in locals():
            stop_results = integration.stop_all_services()
            for service_name, success in stop_results.items():
                status_icon = "✅" if success else "❌"
                print(f"  {status_icon} Stopped {service_name}")
        
        print("👋 Goodbye!")
        
    except Exception as e:
        logger.error(f"Error starting microservice environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())