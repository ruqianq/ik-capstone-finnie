# Contributing to FinnIE

Thank you for your interest in contributing to FinnIE! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/ik-capstone-finnie.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `pytest tests/`
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Google API key

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

3. Run tests:
   ```bash
   pytest tests/ -v
   ```

4. Run the application:
   ```bash
   python -m finnie.main
   ```

## Code Standards

### Python Style

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and small

### Example

```python
def process_query(user_query: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Process user query and return response.
    
    Args:
        user_query: User's question or request
        context: Optional context information
        
    Returns:
        Agent's response
    """
    # Implementation
    pass
```

## Testing

### Writing Tests

- Write tests for all new features
- Maintain test coverage above 80%
- Use pytest fixtures for common setup
- Mock external API calls

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=finnie --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run specific test
pytest tests/test_agents.py::test_agent_initialization
```

## Adding New Agents

To add a new specialist agent:

1. Add agent configuration to `config/agents.json`:
   ```json
   {
     "new_agent": {
       "name": "New Agent",
       "description": "Description of what this agent does",
       "model": "gemini-1.5-flash",
       "system_prompt": "You are a specialist in..."
     }
   }
   ```

2. The agent will be automatically loaded by the system

3. For custom behavior, extend the `FinancialAgent` class:
   ```python
   from finnie.agents import FinancialAgent
   
   class CustomAgent(FinancialAgent):
       async def process(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> str:
           # Custom implementation
           pass
   ```

4. Write tests for your new agent

## Documentation

- Update README.md if adding new features
- Update ARCHITECTURE.md for architectural changes
- Update DEPLOYMENT.md for deployment changes
- Add docstrings to all functions and classes
- Include examples in documentation

## Commit Messages

Use clear and descriptive commit messages:

```
Add budget allocation feature

- Implement budget allocation algorithm
- Add tests for budget calculation
- Update documentation
```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update the README.md with details of changes if appropriate
5. The PR will be merged once approved by maintainers

## Code Review

All submissions require review. We use GitHub pull requests for this purpose. Consult [GitHub Help](https://help.github.com/articles/about-pull-requests/) for more information.

## Bug Reports

When filing a bug report, include:

- Description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Error messages and logs

## Feature Requests

When requesting a feature:

- Describe the feature clearly
- Explain why it would be useful
- Provide examples of how it would be used
- Consider implementation approach

## Questions?

- Open an issue on GitHub
- Check existing issues and documentation
- Review the ARCHITECTURE.md for system design

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by opening an issue.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
