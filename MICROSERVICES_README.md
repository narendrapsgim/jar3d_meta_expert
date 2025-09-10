# Jar3d Microservice Agent Architecture

This document describes the microservice agent orchestration system implemented in Jar3d, similar to OpenHands' microagent architecture.

## 🏗️ Architecture Overview

The microservice architecture extends Jar3d with dynamic agent provisioning, orchestration, and scalable deployment capabilities:

```
┌─────────────────────────────────────────────────────────────┐
│                    Jar3d Application                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Meta Agent    │  │  Enhanced Base  │  │ Integration  │ │
│  │  (Orchestrator) │  │     Agents      │  │    Layer     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                  Microservice Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  API Gateway    │  │  Orchestrator   │  │   Registry   │ │
│  │   (FastAPI)     │  │   (Workflow)    │  │  (Dynamic)   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                 Microservice Agents                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Web Search     │  │ Content Gen     │  │ Data Analysis│ │
│  │   Service       │  │   Service       │  │   Service    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                Infrastructure Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │     Docker      │  │     Redis       │  │    Consul    │ │
│  │  Containers     │  │   (Caching)     │  │ (Discovery)  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Key Features

### 1. Dynamic Agent Provisioning
- **Prompt-based Creation**: Create agents from natural language descriptions
- **Template System**: Pre-built templates for common agent types
- **Configuration Management**: YAML/Markdown configuration files
- **Runtime Registration**: Add/remove agents without system restart

### 2. Microservice Orchestration
- **Workflow Coordination**: Multi-agent workflows with dependencies
- **Task Queue Management**: Asynchronous task processing
- **Load Balancing**: Distribute tasks across agent instances
- **Fault Tolerance**: Graceful handling of service failures

### 3. Scalable Deployment
- **Container-based**: Docker containers for each microservice
- **Service Discovery**: Automatic service registration and discovery
- **Health Monitoring**: Built-in health checks and monitoring
- **Resource Management**: CPU and memory limits per service

## 📁 Directory Structure

```
jar3d_meta_expert/
├── microservices/                    # Microservice architecture
│   ├── __init__.py
│   ├── agent_registry.py            # Enhanced agent registry
│   ├── orchestrator.py              # Multi-agent orchestration
│   ├── api_gateway.py               # RESTful API gateway
│   ├── microagent_framework.py      # Prompt-based agent creation
│   ├── enhanced_agent_base.py       # Enhanced base agents
│   ├── integration.py               # Integration with existing system
│   ├── cli.py                       # Command-line management tool
│   └── containers/                  # Docker containers
│       ├── base_microservice.py     # Base microservice template
│       ├── Dockerfile.microservice  # Microservice Dockerfile
│       ├── Dockerfile.gateway       # API Gateway Dockerfile
│       └── requirements-microservice.txt
├── .jar3d/                          # Configuration directory
│   ├── microagents/                 # Microagent definitions
│   │   ├── web_researcher.md        # Web research specialist
│   │   ├── content_specialist.md    # Content creation specialist
│   │   └── data_analyst.md          # Data analysis specialist
│   └── templates/                   # Agent templates
├── scripts/
│   └── start_microservices.py       # Startup script
└── docker-compose.yaml              # Multi-container deployment
```

## 🛠️ Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Microservice Environment

```bash
# Create microagent directory
mkdir -p .jar3d/microagents

# Start microservice environment
python scripts/start_microservices.py
```

### 3. Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Start specific services
docker-compose up api-gateway web-search-service
```

## 🎯 Usage Examples

### 1. Create Microagent from Prompt

```bash
# Using CLI
python -m microservices.cli create research_assistant \
  --prompt "Create an agent that can research academic papers and summarize findings"

# Using Python API
from microservices.integration import get_microservice_integration

integration = get_microservice_integration()
agent_name = integration.create_microagent_from_prompt(
    name="research_assistant",
    prompt="Create an agent that can research academic papers and summarize findings",
    capabilities=["web_search", "summarization", "academic_research"]
)
```

### 2. Submit Tasks to Microservices

```bash
# Using CLI
python -m microservices.cli task web_search_agent \
  "Search for recent developments in AI safety" \
  --wait

# Using API
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "web_search_agent",
    "instruction": "Search for recent developments in AI safety",
    "context": {}
  }'
```

### 3. Execute Multi-Agent Workflows

```python
import asyncio
from microservices.integration import get_microservice_integration

async def run_research_workflow():
    integration = get_microservice_integration()
    
    result = await integration.execute_microservice_workflow(
        requirements="Research and create a comprehensive report on renewable energy trends",
        context={"format": "report", "length": "detailed"}
    )
    
    print(result)

asyncio.run(run_research_workflow())
```

## 🔧 Configuration

### Microagent Configuration (Markdown Format)

```markdown
---
name: custom_agent
description: Custom agent description
trigger_type: always  # always, on_demand, repository
capabilities:
  - web_search
  - data_analysis
dependencies:
  - search_engine
  - database
environment_vars:
  API_KEY: "your_api_key"
resource_limits:
  memory: "512Mi"
  cpu: "0.5"
---

# Agent Instructions

Your detailed agent instructions go here...
```

### YAML Configuration

```yaml
name: custom_agent
description: Custom agent description
prompt: |
  You are a custom agent with specific capabilities.
  Handle tasks related to your domain expertise.
trigger_type: always
capabilities:
  - web_search
  - data_analysis
dependencies:
  - search_engine
environment_vars:
  API_KEY: "your_api_key"
resource_limits:
  memory: "512Mi"
  cpu: "0.5"
```

## 🌐 API Endpoints

### Agent Management
- `GET /agents` - List all agents
- `POST /agents` - Create new agent
- `GET /agents/{name}` - Get agent details
- `DELETE /agents/{name}` - Delete agent

### Service Management
- `GET /services` - List active services
- `POST /services/{name}/start` - Start service
- `POST /services/{name}/stop` - Stop service
- `GET /services/{name}` - Get service status

### Task Execution
- `POST /tasks` - Submit task
- `GET /tasks/{task_id}` - Get task status
- `GET /tasks` - List active tasks
- `GET /tasks/history` - Get task history

### Workflow Execution
- `POST /workflows/execute` - Execute workflow

### System Management
- `GET /health` - Health check
- `GET /registry/export` - Export registry
- `POST /registry/import` - Import registry

## 🔍 Monitoring & Management

### CLI Commands

```bash
# List all agents
python -m microservices.cli list

# List active services
python -m microservices.cli services

# Start/stop services
python -m microservices.cli start web_search_agent
python -m microservices.cli stop web_search_agent

# Submit tasks
python -m microservices.cli task web_search_agent "Search for AI news" --wait

# Manage templates
python -m microservices.cli templates

# Export/import configuration
python -m microservices.cli export config.json
python -m microservices.cli import config.json
```

### Health Monitoring

```bash
# Check API Gateway health
curl http://localhost:8000/health

# Check individual service health
curl http://localhost:8001/health  # Web Search Service
curl http://localhost:8002/health  # Content Generator Service
curl http://localhost:8003/health  # Data Analysis Service
```

## 🔄 Integration with Existing Jar3d

The microservice architecture seamlessly integrates with the existing Jar3d system:

1. **Enhanced Agents**: Existing agents are automatically enhanced with microservice capabilities
2. **Hybrid Execution**: Agents can execute locally or delegate to microservices
3. **Workflow Integration**: Microservices participate in existing LangGraph workflows
4. **Backward Compatibility**: All existing functionality remains unchanged

### Integration Points

```python
# In main.py - automatic integration
from microservices.integration import initialize_microservices

# Initialize microservices
microservice_integration = initialize_microservices()

# Enhance existing agents
enhanced_team = microservice_integration.get_enhanced_agents_for_workflow(agent_team)
```

## 🚀 Deployment Options

### Development Mode
```bash
# Start with Python
python scripts/start_microservices.py

# Or start main application with microservice support
python main.py
```

### Production Mode
```bash
# Docker Compose deployment
docker-compose up -d

# Kubernetes deployment (requires k8s manifests)
kubectl apply -f k8s/
```

### Cloud Deployment
- **AWS**: Use ECS/EKS with Application Load Balancer
- **GCP**: Use Cloud Run or GKE with Cloud Load Balancing
- **Azure**: Use Container Instances or AKS with Application Gateway

## 🔒 Security Considerations

1. **API Authentication**: Implement JWT or API key authentication
2. **Network Security**: Use TLS/SSL for all communications
3. **Container Security**: Run containers with non-root users
4. **Resource Limits**: Set appropriate CPU and memory limits
5. **Input Validation**: Validate all inputs to prevent injection attacks

## 🐛 Troubleshooting

### Common Issues

1. **Service Discovery Failures**
   ```bash
   # Check Consul status
   curl http://localhost:8500/v1/status/leader
   
   # Restart services
   docker-compose restart consul
   ```

2. **Task Execution Timeouts**
   ```bash
   # Check orchestrator logs
   docker-compose logs api-gateway
   
   # Increase timeout in configuration
   ```

3. **Memory Issues**
   ```bash
   # Check resource usage
   docker stats
   
   # Adjust resource limits in docker-compose.yaml
   ```

## 📈 Performance Optimization

1. **Caching**: Use Redis for caching frequent requests
2. **Load Balancing**: Deploy multiple instances of high-demand services
3. **Resource Tuning**: Optimize CPU and memory allocations
4. **Connection Pooling**: Use connection pools for database access
5. **Monitoring**: Implement comprehensive monitoring and alerting

## 🤝 Contributing

1. **Adding New Microservices**: Extend `base_microservice.py`
2. **Creating Templates**: Add templates to `.jar3d/templates/`
3. **Enhancing Orchestration**: Modify `orchestrator.py`
4. **API Extensions**: Add endpoints to `api_gateway.py`

## 📚 Additional Resources

- [OpenHands Microagents Documentation](https://github.com/All-Hands-AI/OpenHands)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

---

This microservice architecture transforms Jar3d into a scalable, dynamic agent orchestration platform while maintaining full backward compatibility with existing functionality.