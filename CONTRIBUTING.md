# Contributing Guidelines

## Welcome Contributors! 🎉

Thank you for your interest in contributing to the Huawei Analytics UI Generator! This document provides comprehensive guidelines for contributing to the project, ensuring consistency, quality, and smooth collaboration.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Documentation Standards](#documentation-standards)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful, constructive, and professional in all interactions.

## Getting Started

### Prerequisites

- Python 3.8+ (3.11 recommended)
- Git for version control
- API keys for OpenRouter and OpenAI
- Basic understanding of FastAPI, LangChain, and AI systems

### Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/your-username/huawei_agent_poc_openai.git
cd huawei_agent_poc_openai

# Add upstream remote
git remote add upstream https://github.com/original-repo/huawei_agent_poc_openai.git
```

## Development Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install black isort flake8 pytest pytest-asyncio httpx
```

### 2. Environment Variables

Create a `.env` file with your API keys:

```env
# Required API keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional development settings
LOG_LEVEL=DEBUG
DEVELOPMENT_MODE=true
```

### 3. Data Setup

Ensure the data directory structure exists:

```bash
mkdir -p data/user_activity
mkdir -p data/ui_patterns
```

## Code Style Guidelines

### Python Code Style

We follow **PEP 8** with the following specific guidelines:

#### Formatting
- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces (no tabs)
- **String quotes**: Double quotes preferred
- **Import organization**: isort with Black compatibility

#### Naming Conventions
```python
# Classes: PascalCase
class AnalyticsUIAgent:
    pass

# Functions and variables: snake_case
def generate_ui(user_query: str) -> Dict:
    api_response = None

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TEMPERATURE = 0.7

# Private methods: leading underscore
def _internal_method(self):
    pass
```

#### Type Hints
All functions must include type hints:

```python
from typing import Dict, List, Optional, Union

def process_query(
    query: str, 
    user_data: Dict[str, Any], 
    options: Optional[Dict] = None
) -> Dict[str, Union[str, bool]]:
    """Process user query with proper type hints."""
    pass
```

### Documentation Style

#### Function Docstrings
Use Google-style docstrings:

```python
def generate_ui(query: str, user_data: Dict) -> Dict:
    """
    Generate UI JSON from natural language query.
    
    This function processes user queries and generates appropriate
    Jetpack Compose UI structures based on the provided data.
    
    Args:
        query (str): Natural language query describing desired UI.
        user_data (Dict): User activity data for contextualization.
    
    Returns:
        Dict: Complete Jetpack Compose UI JSON structure.
    
    Raises:
        ValueError: If query is empty or user_data is invalid.
        APIError: If external API calls fail.
    
    Example:
        >>> ui = generate_ui("show whatsapp usage", user_data)
        >>> print(ui["type"])
        "Screen"
    """
    pass
```

#### Class Docstrings
```python
class RAGManager:
    """
    Manager for Retrieval-Augmented Generation operations.
    
    This class orchestrates vector storage and semantic search for user
    activity data, enabling intelligent context retrieval for UI generation.
    
    Attributes:
        embeddings (CustomOpenAIEmbeddings): Text embedding service.
        vector_store (Optional[Chroma]): Vector database instance.
    
    Example:
        >>> rag = RAGManager(api_key="your-key")
        >>> rag.initialize_vector_store("data.txt")
        >>> results = rag.query_user_data("WhatsApp usage")
    """
    pass
```

### Code Organization

#### File Structure
```python
# File header with module documentation
"""
Module Description

Brief description of module purpose and key components.
"""

# Standard library imports
import json
import os
from typing import Dict, List

# Third-party imports
import requests
from fastapi import FastAPI
from langchain.embeddings import Embeddings

# Local imports
from src.openrouter_llm import OpenRouterLLM
from src.rag import RAGManager

# Constants
DEFAULT_MODEL = "claude-sonnet-4"
MAX_RETRIES = 3

# Classes and functions
class ExampleClass:
    pass

def example_function():
    pass
```

## Testing Requirements

### Test Structure

Create tests in the `tests/` directory:

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_api.py              # API endpoint tests
├── test_analytics_agent.py  # Agent functionality tests
├── test_rag.py              # RAG system tests
├── test_openrouter_llm.py   # LLM integration tests
└── integration/             # End-to-end tests
    ├── __init__.py
    └── test_full_pipeline.py
```

### Test Guidelines

#### Unit Tests
```python
import pytest
from unittest.mock import Mock, patch
from src.analytics_agent import AnalyticsUIAgent

class TestAnalyticsAgent:
    """Test suite for Analytics UI Agent."""
    
    @pytest.fixture
    def mock_rag_tool(self):
        """Create mock RAG tool for testing."""
        tool = Mock()
        tool._run.return_value = "Mock user data"
        return tool
    
    @pytest.fixture
    def agent(self, mock_rag_tool):
        """Create agent instance with mocked dependencies."""
        return AnalyticsUIAgent(
            rag_tools=[mock_rag_tool],
            llm=Mock()
        )
    
    def test_analyze_intent_whatsapp_query(self, agent):
        """Test intent analysis for WhatsApp queries."""
        intent = agent.analyze_intent("show me my whatsapp usage today")
        
        assert intent['app'] == 'whatsapp'
        assert intent['timeframe'] == 'today'
        assert intent['ui_request_type'] == 'data_visualization'
    
    def test_analyze_intent_simple_ui_query(self, agent):
        """Test intent analysis for simple UI requests."""
        intent = agent.analyze_intent("create a login page")
        
        assert intent['app'] == 'general'
        assert intent['ui_request_type'] == 'simple_ui'
```

#### Integration Tests
```python
import pytest
import httpx
from fastapi.testclient import TestClient
from api import app

class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_generate_ui_endpoint(self, client):
        """Test complete UI generation pipeline."""
        response = client.post(
            "/generate-ui",
            json={"query": "show me my whatsapp usage today"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "ui" in data
        assert data["ui"]["type"] == "Screen"
```

#### Test Configuration
Create `conftest.py`:

```python
import pytest
import os
from unittest.mock import Mock

@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    os.environ["OPENROUTER_API_KEY"] = "test-key"
    os.environ["OPENAI_API_KEY"] = "test-key"
    yield
    # Cleanup after tests

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = Mock()
    client.embeddings.create.return_value.data = [
        Mock(embedding=[0.1] * 1536)
    ]
    return client
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v

# Run only fast tests (skip integration)
pytest -m "not integration"
```

## Commit Guidelines

### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to build process or auxiliary tools

#### Examples
```bash
# Feature addition
git commit -m "feat(api): add health check endpoint with component status"

# Bug fix
git commit -m "fix(rag): handle empty query results gracefully"

# Documentation
git commit -m "docs(readme): update installation instructions for Python 3.11"

# Breaking change
git commit -m "feat(agent)!: redesign intent analysis with new classification system

BREAKING CHANGE: Intent analysis now returns different structure.
Migration guide available in MIGRATION.md"
```

## Pull Request Process

### Before Submitting

1. **Update your fork**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Run quality checks**:
   ```bash
   # Format code
   black src/ tests/
   isort src/ tests/
   
   # Lint code
   flake8 src/ tests/
   
   # Run tests
   pytest
   ```

### Pull Request Template

```markdown
## Description
Brief description of the changes and their purpose.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Screenshots (if applicable)
Include screenshots or examples of the changes.
```

### Review Process

1. **Automated Checks**: All CI checks must pass
2. **Code Review**: At least one maintainer approval required
3. **Testing**: Comprehensive test coverage for new features
4. **Documentation**: Updates to relevant documentation files

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Send request to '...'
2. With parameters '...'
3. See error

**Expected Behavior**
A clear description of what you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g. macOS 12.0]
- Python version: [e.g. 3.11.0]
- Package versions: [relevant package versions]

**API Logs**
```
Include relevant log output
```

**Additional Context**
Add any other context about the problem here.
```

### Feature Requests

```markdown
**Feature Description**
A clear and concise description of the desired feature.

**Use Case**
Describe the problem this feature would solve.

**Proposed Solution**
A clear description of what you want to happen.

**Alternatives Considered**
A description of any alternative solutions or features you've considered.

**Additional Context**
Add any other context or screenshots about the feature request here.
```

## Documentation Standards

### README Updates

When adding new features, update the README with:
- Installation instructions (if dependencies change)
- Usage examples
- Configuration options
- API changes

### API Documentation

- Update `API_README.md` for endpoint changes
- Include request/response examples
- Document error conditions
- Update OpenAPI schema in FastAPI

### Code Documentation

- All public methods must have docstrings
- Complex algorithms need inline comments
- Architecture decisions should be documented in `ARCHITECTURE.md`

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

### Release Checklist

1. **Update version numbers** in relevant files
2. **Update CHANGELOG.md** with release notes
3. **Create release branch**: `git checkout -b release/v1.2.0`
4. **Run full test suite**: `pytest`
5. **Create pull request** for release branch
6. **After approval, tag release**: `git tag v1.2.0`
7. **Push tags**: `git push --tags`

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and community support
- **Documentation**: Comprehensive guides and API reference

### Development Questions

For development-related questions:
1. Check existing documentation
2. Search closed issues
3. Create new issue with detailed context

## Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes for significant contributions
- GitHub contributor insights

Thank you for contributing to the Huawei Analytics UI Generator! 🚀