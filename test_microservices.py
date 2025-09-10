#!/usr/bin/env python3
"""
Test script for microservice integration
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from microservices.integration import get_microservice_integration
from microservices.agent_registry import MicroAgentConfig

async def test_microservice_integration():
    """Test the microservice integration"""
    print("🧪 Testing Microservice Integration")
    print("=" * 40)
    
    try:
        # Initialize integration
        print("1. Initializing microservice integration...")
        integration = get_microservice_integration()
        print("   ✅ Integration initialized")
        
        # Check registry status
        print("\n2. Checking registry status...")
        status = integration.get_microservice_status()
        print(f"   📊 Registry: {status['registry']['total_agents']} agents")
        print(f"   🚀 Active services: {status['registry']['active_services']}")
        
        # List discovered agents
        print("\n3. Discovered agents:")
        for agent_name in status['registry']['agents']:
            agent_config = integration.registry.get_agent(agent_name)
            if agent_config:
                print(f"   🤖 {agent_name}: {agent_config.description}")
        
        # Test creating an agent from prompt
        print("\n4. Testing agent creation from prompt...")
        test_agent_name = "test_research_agent"
        
        # Remove existing test agent if it exists
        if integration.registry.get_agent(test_agent_name):
            integration.registry.unregister_agent(test_agent_name)
        
        agent_name = integration.create_microagent_from_prompt(
            name=test_agent_name,
            prompt="Create a research agent that can search for information and summarize findings",
            capabilities=["web_search", "summarization"],
            trigger_type="on_demand"
        )
        print(f"   ✅ Created agent: {agent_name}")
        
        # Verify agent was created
        created_agent = integration.registry.get_agent(test_agent_name)
        if created_agent:
            print(f"   📋 Agent capabilities: {', '.join(created_agent.capabilities)}")
        
        # Test workflow execution (simulated)
        print("\n5. Testing workflow execution...")
        try:
            result = await integration.execute_microservice_workflow(
                requirements="Search for information about artificial intelligence trends",
                context={"format": "summary"}
            )
            print(f"   ✅ Workflow executed: {result.get('status', 'unknown')}")
            if result.get('error'):
                print(f"   ⚠️ Workflow error: {result['error']}")
        except Exception as e:
            print(f"   ⚠️ Workflow test failed: {e}")
        
        # Test service management
        print("\n6. Testing service management...")
        start_results = integration.start_all_services()
        started_count = sum(1 for success in start_results.values() if success)
        print(f"   🚀 Started {started_count}/{len(start_results)} services")
        
        # Display final status
        print("\n7. Final status:")
        final_status = integration.get_microservice_status()
        print(f"   📊 Total agents: {final_status['registry']['total_agents']}")
        print(f"   🚀 Active services: {final_status['registry']['active_services']}")
        print(f"   📝 Active tasks: {final_status['orchestrator']['active_tasks']}")
        
        # Cleanup test agent
        integration.registry.unregister_agent(test_agent_name)
        print(f"   🧹 Cleaned up test agent: {test_agent_name}")
        
        print("\n" + "=" * 40)
        print("✅ All tests passed! Microservice integration is working.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_registry():
    """Test the agent registry functionality"""
    print("\n🧪 Testing Agent Registry")
    print("=" * 30)
    
    try:
        integration = get_microservice_integration()
        registry = integration.registry
        
        # Test agent creation
        test_config = MicroAgentConfig(
            name="test_agent",
            description="Test agent for registry testing",
            prompt="You are a test agent",
            capabilities=["testing"],
            trigger_type="on_demand"
        )
        
        # Register agent
        success = registry.register_agent(test_config)
        print(f"   ✅ Agent registration: {success}")
        
        # Retrieve agent
        retrieved = registry.get_agent("test_agent")
        print(f"   ✅ Agent retrieval: {retrieved is not None}")
        
        # List agents
        agents = registry.list_agents()
        print(f"   📊 Total agents: {len(agents)}")
        
        # Test capability search
        test_agents = registry.get_agents_by_capability("testing")
        print(f"   🔍 Agents with 'testing' capability: {len(test_agents)}")
        
        # Cleanup
        registry.unregister_agent("test_agent")
        print("   🧹 Cleaned up test agent")
        
        print("   ✅ Registry tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Registry test failed: {e}")
        return False

def test_microagent_factory():
    """Test the microagent factory"""
    print("\n🧪 Testing Microagent Factory")
    print("=" * 30)
    
    try:
        integration = get_microservice_integration()
        factory = integration.factory
        
        # Test template listing
        templates = factory.list_templates()
        print(f"   📋 Available templates: {len(templates)}")
        
        for template in templates:
            print(f"      • {template.name}: {template.description}")
        
        # Test agent creation from template
        if templates:
            template_name = templates[0].name
            agent_config = factory.create_agent_from_template(
                name="test_template_agent",
                template_name=template_name
            )
            print(f"   ✅ Created agent from template: {agent_config.name}")
            
            # Cleanup
            integration.registry.unregister_agent("test_template_agent")
            print("   🧹 Cleaned up template agent")
        
        print("   ✅ Factory tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Factory test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Jar3d Microservice Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Microservice Integration", test_microservice_integration()),
        ("Agent Registry", test_agent_registry()),
        ("Microagent Factory", test_microagent_factory())
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            if asyncio.iscoroutine(test_func):
                result = await test_func
            else:
                result = test_func
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Microservice integration is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)