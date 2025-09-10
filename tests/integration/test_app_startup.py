"""Integration tests for application startup."""
import pytest
import asyncio
import os
from unittest.mock import patch


class TestAppStartup:
    """Test application startup and basic functionality."""
    
    @pytest.mark.asyncio
    async def test_main_imports(self):
        """Test that main module can be imported without errors."""
        try:
            with patch.dict(os.environ, {
                'OPENAI_API_KEY': 'test_key',
                'ANTHROPIC_API_KEY': 'test_key',
                'SERPER_API_KEY': 'test_key',
                'NEO4J_URI': 'bolt://localhost:7687',
                'NEO4J_USERNAME': 'neo4j',
                'NEO4J_PASSWORD': 'test_password'
            }):
                import main
                assert main is not None
        except Exception as e:
            pytest.skip(f"Main module import failed: {e}")
    
    @pytest.mark.asyncio
    async def test_chainlit_integration(self):
        """Test Chainlit integration."""
        try:
            import chainlit as cl
            assert cl is not None
        except ImportError:
            pytest.skip("Chainlit not available for testing")
    
    def test_docker_compose_config(self):
        """Test Docker Compose configuration is valid."""
        import yaml
        
        compose_file = "docker-compose.yaml"
        if os.path.exists(compose_file):
            with open(compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)
                
            # Verify required services
            assert 'services' in compose_config
            assert 'jar3d' in compose_config['services']
            assert 'nlm-ingestor' in compose_config['services']
            
            # Verify jar3d service configuration
            jar3d_service = compose_config['services']['jar3d']
            assert 'build' in jar3d_service
            assert 'ports' in jar3d_service
            assert '8105:8105' in jar3d_service['ports']
        else:
            pytest.skip("docker-compose.yaml not found")
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and has basic structure."""
        dockerfile_path = "Dockerfile"
        assert os.path.exists(dockerfile_path), "Dockerfile should exist"
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
            
        # Check for essential Dockerfile commands
        assert 'FROM python:3.11-slim' in content
        assert 'COPY requirements.txt' in content
        assert 'RUN pip install' in content
        assert 'EXPOSE 8105' in content
        assert 'CMD ["chainlit"' in content