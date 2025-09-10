"""
Base Microservice Container
Template for creating containerized microservice agents
"""
import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskRequest(BaseModel):
    """Request model for microservice tasks"""
    instruction: str
    context: Dict[str, Any] = {}
    timeout: int = 300

class TaskResponse(BaseModel):
    """Response model for microservice tasks"""
    status: str
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str

class BaseMicroService:
    """
    Base class for microservice agents
    """
    
    def __init__(self, name: str, description: str, capabilities: list = None):
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.app = FastAPI(
            title=f"{name} Microservice",
            description=description,
            version="1.0.0"
        )
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "name": self.name,
                "description": self.description,
                "capabilities": self.capabilities,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/info")
        async def get_info():
            """Get microservice information"""
            return {
                "name": self.name,
                "description": self.description,
                "capabilities": self.capabilities,
                "version": "1.0.0"
            }
        
        @self.app.post("/execute", response_model=TaskResponse)
        async def execute_task(request: TaskRequest):
            """Execute a task"""
            start_time = datetime.now()
            
            try:
                result = await self.process_task(request.instruction, request.context)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return TaskResponse(
                    status="success",
                    result=result,
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"Error executing task: {e}")
                
                return TaskResponse(
                    status="error",
                    error=str(e),
                    execution_time=execution_time,
                    timestamp=datetime.now().isoformat()
                )
    
    async def process_task(self, instruction: str, context: Dict[str, Any]) -> Any:
        """
        Process a task - to be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement process_task method")
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the microservice"""
        logger.info(f"Starting {self.name} microservice on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

class WebSearchMicroService(BaseMicroService):
    """
    Web search microservice agent
    """
    
    def __init__(self):
        super().__init__(
            name="web_search_agent",
            description="Performs web searches and returns results",
            capabilities=["web_search", "information_retrieval"]
        )
    
    async def process_task(self, instruction: str, context: Dict[str, Any]) -> Any:
        """Process web search task"""
        # Simulate web search
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Extract search query from instruction
        query = instruction.replace("search for", "").replace("find", "").strip()
        
        # Simulate search results
        results = [
            {
                "title": f"Result 1 for '{query}'",
                "url": "https://example.com/result1",
                "snippet": f"This is a sample search result for {query}. It contains relevant information about the topic."
            },
            {
                "title": f"Result 2 for '{query}'",
                "url": "https://example.com/result2",
                "snippet": f"Another relevant result for {query} with additional details and insights."
            },
            {
                "title": f"Result 3 for '{query}'",
                "url": "https://example.com/result3",
                "snippet": f"Third search result providing more information about {query}."
            }
        ]
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "search_time": 0.5
        }

class ContentGeneratorMicroService(BaseMicroService):
    """
    Content generation microservice agent
    """
    
    def __init__(self):
        super().__init__(
            name="content_generator_agent",
            description="Generates various types of content",
            capabilities=["content_generation", "writing", "summarization"]
        )
    
    async def process_task(self, instruction: str, context: Dict[str, Any]) -> Any:
        """Process content generation task"""
        # Simulate content generation
        await asyncio.sleep(1.0)  # Simulate processing time
        
        # Determine content type from instruction
        if "summary" in instruction.lower():
            content_type = "summary"
            content = f"This is a generated summary based on the instruction: {instruction}"
        elif "article" in instruction.lower():
            content_type = "article"
            content = f"# Generated Article\n\nThis is a generated article based on: {instruction}\n\n## Introduction\n\nContent goes here...\n\n## Conclusion\n\nSummary of key points."
        elif "email" in instruction.lower():
            content_type = "email"
            content = f"Subject: Generated Email\n\nDear Recipient,\n\nThis email was generated based on: {instruction}\n\nBest regards,\nContent Generator"
        else:
            content_type = "general"
            content = f"Generated content for: {instruction}"
        
        return {
            "content_type": content_type,
            "content": content,
            "word_count": len(content.split()),
            "generation_time": 1.0
        }

class DataAnalysisMicroService(BaseMicroService):
    """
    Data analysis microservice agent
    """
    
    def __init__(self):
        super().__init__(
            name="data_analysis_agent",
            description="Performs data analysis and processing",
            capabilities=["data_analysis", "statistics", "visualization"]
        )
    
    async def process_task(self, instruction: str, context: Dict[str, Any]) -> Any:
        """Process data analysis task"""
        # Simulate data analysis
        await asyncio.sleep(1.5)  # Simulate processing time
        
        # Extract data from context if available
        data = context.get("data", [])
        
        if not data:
            # Generate sample data
            data = [
                {"category": "A", "value": 10},
                {"category": "B", "value": 15},
                {"category": "C", "value": 8},
                {"category": "D", "value": 12}
            ]
        
        # Perform basic analysis
        values = [item["value"] for item in data if isinstance(item, dict) and "value" in item]
        
        if values:
            analysis = {
                "total": sum(values),
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values)
            }
        else:
            analysis = {"error": "No numeric data found for analysis"}
        
        return {
            "instruction": instruction,
            "data_points": len(data),
            "analysis": analysis,
            "processing_time": 1.5
        }

# Factory function to create microservices
def create_microservice(service_type: str) -> BaseMicroService:
    """Create a microservice based on type"""
    services = {
        "web_search": WebSearchMicroService,
        "content_generator": ContentGeneratorMicroService,
        "data_analysis": DataAnalysisMicroService
    }
    
    if service_type not in services:
        raise ValueError(f"Unknown service type: {service_type}")
    
    return services[service_type]()

if __name__ == "__main__":
    # Get service type from environment variable
    service_type = os.getenv("SERVICE_TYPE", "web_search")
    port = int(os.getenv("PORT", "8000"))
    
    try:
        service = create_microservice(service_type)
        service.run(port=port)
    except Exception as e:
        logger.error(f"Failed to start microservice: {e}")
        exit(1)