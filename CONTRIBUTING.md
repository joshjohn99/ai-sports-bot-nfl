# Contributing to AI Sports Bot NFL

Thank you for your interest in contributing to the AI Sports Bot NFL project! This document provides guidelines and information for contributors.

## 🎯 How to Contribute

### Reporting Issues
- Use the [GitHub Issues](https://github.com/yourusername/ai-sports-bot-nfl/issues) page
- Search existing issues before creating a new one
- Provide detailed information including:
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (Python version, OS, etc.)
  - Error messages or logs

### Suggesting Features
- Open a [GitHub Discussion](https://github.com/yourusername/ai-sports-bot-nfl/discussions)
- Explain the use case and benefits
- Consider implementation complexity
- Check if it aligns with project goals

### Code Contributions

#### 1. Fork and Clone
```bash
git clone https://github.com/yourusername/ai-sports-bot-nfl.git
cd ai-sports-bot-nfl
```

#### 2. Set Up Development Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

#### 3. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

#### 4. Make Changes
- Follow the coding standards (see below)
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

#### 5. Commit and Push
```bash
git add .
git commit -m "feat: add new feature description"
git push origin feature/your-feature-name
```

#### 6. Create Pull Request
- Use the GitHub web interface
- Provide a clear description of changes
- Link to related issues
- Wait for review and address feedback

## 📝 Coding Standards

### Python Style
- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [flake8](https://flake8.pycqa.org/) for linting
- Maximum line length: 88 characters (Black default)

### Code Organization
```python
# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import requests
from pydantic import BaseModel

# Local imports
from sports_bot.config.api_config import api_config
from sports_bot.utils.helpers import format_player_name
```

### Documentation
- Use docstrings for all functions, classes, and modules
- Follow [Google Style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) docstrings
- Include type hints for all function parameters and return values

```python
def fetch_player_stats(player_name: str, season: str) -> Dict[str, Any]:
    """
    Fetch statistics for a specific player and season.
    
    Args:
        player_name: The player's full name
        season: The season year (e.g., "2024")
        
    Returns:
        Dictionary containing player statistics
        
    Raises:
        ValueError: If player name is invalid
        APIError: If API request fails
    """
    pass
```

### Testing
- Write tests for all new functionality
- Use `pytest` for testing framework
- Aim for >90% code coverage
- Include both unit tests and integration tests

```python
def test_fetch_player_stats():
    """Test player statistics fetching."""
    result = fetch_player_stats("Josh Allen", "2024")
    assert result["success"] is True
    assert "passing_yards" in result["data"]
```

## 🏗️ Architecture Guidelines

### Adding New Sports
1. Update `sport_registry.py` with new sport configuration
2. Create sport-specific adapter if needed
3. Add tests for the new sport
4. Update documentation

### Adding New Query Types
1. Add to `QueryType` enum in `query_types.py`
2. Implement execution logic in `QueryExecutor`
3. Add response formatting in `ResponseFormatter`
4. Create comprehensive tests

### Adding New Agents
1. Create agent class in `src/sports_bot/agents/`
2. Follow the existing agent interface patterns
3. Add integration with the agent bridge
4. Include proper error handling and logging

## 🧪 Testing Guidelines

### Running Tests
```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_phase1_comprehensive.py -v

# Integration tests
python test_integration_final.py

# With coverage
python -m pytest tests/ --cov=src/sports_bot --cov-report=html
```

### Test Categories
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows
- **Performance Tests**: Test API efficiency and caching

### Writing Good Tests
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies (APIs, databases)
- Keep tests fast and isolated

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts

### Commit Message Convention
Use [Conventional Commits](https://conventionalcommits.org/):

```
feat: add support for NBA statistics
fix: resolve player name disambiguation issue
docs: update API configuration guide
test: add tests for multi-player comparisons
refactor: improve caching efficiency
```

### Review Process
1. Automated checks must pass (tests, linting)
2. At least one maintainer review required
3. Address all feedback before merge
4. Squash commits if requested

## 🎯 Development Focus Areas

### High Priority
- **Multi-sport support**: Expanding beyond NFL
- **Performance optimization**: Reducing API calls and latency
- **Error handling**: Improving user experience with better error messages
- **Documentation**: Comprehensive guides and examples

### Medium Priority
- **Web interface**: React/FastAPI frontend
- **Real-time data**: Live game statistics
- **Advanced analytics**: Predictive modeling and trends
- **Mobile support**: Native app development

### Low Priority
- **Voice integration**: Alexa/Google Assistant
- **Social features**: Sharing and community
- **Enterprise features**: Advanced team management tools

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Celebrate diverse perspectives

### Communication
- Use GitHub Issues for bugs and feature requests
- Use GitHub Discussions for questions and ideas
- Be patient with response times
- Provide context and details in communications

## 📚 Resources

### Documentation
- [Project Wiki](https://github.com/yourusername/ai-sports-bot-nfl/wiki)
- [Architecture Overview](docs/architecture/)
- [API Documentation](docs/api/)

### External Resources
- [LangChain Documentation](https://langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [RapidAPI NFL Data](https://rapidapi.com/api-sports/api/nfl-api-data)

### Development Tools
- [Black Code Formatter](https://black.readthedocs.io/)
- [flake8 Linter](https://flake8.pycqa.org/)
- [pytest Testing Framework](https://pytest.org/)
- [mypy Type Checker](https://mypy.readthedocs.io/)

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Annual contributor appreciation posts

Thank you for helping make AI Sports Bot NFL better! 🏈🤖 