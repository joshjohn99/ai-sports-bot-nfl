# 📁 Project Structure

This document explains the organized structure of the AI Sports Bot NFL project.

## 🏗️ Directory Layout

```
sports_bot_beta/
├── README.md                    # Main project documentation
├── requirements.txt             # Python dependencies
├── main.py                     # Main entry point
├── .env                        # Environment variables (not in git)
├── .gitignore                  # Git ignore patterns
│
├── src/                        # Source code
│   └── sports_bot/
│       ├── core/               # Core business logic
│       │   ├── sports_agents.py    # Main agent orchestration
│       │   ├── stat_retriever.py   # API data retrieval
│       │   ├── query_types.py      # Query classification
│       │   └── response_formatter.py # Response formatting
│       │
│       ├── agents/             # AI agents and debate engine
│       │   ├── debate_agent.py      # LLM debate generation
│       │   └── debate_integration.py # Debate system integration
│       │
│       ├── config/             # Configuration
│       │   └── api_config.py        # API endpoints and settings
│       │
│       └── utils/              # Utility functions
│           └── agent_client.py      # Agent client utilities
│
├── tests/                      # Test suite
│   ├── test_phase1_comprehensive.py # Full feature tests
│   ├── test_enhanced_processing.py  # Enhanced processing tests
│   └── test_phase1.py              # Basic architecture tests
│
├── data/                       # Data storage
│   ├── cache/                  # API response cache
│   │   └── api_response_*.json     # Cached API responses
│   └── samples/                # Sample data files
│       ├── resp.json               # Sample API response
│       └── teamreps.json           # Sample team roster data
│
└── docs/                       # Documentation
    └── STRUCTURE.md            # This file
```

## 🎯 Module Responsibilities

### Core Modules (`src/sports_bot/core/`)

- **`sports_agents.py`**: Main orchestration, NLU agents, query planning
- **`stat_retriever.py`**: API integration, data fetching, player lookup
- **`query_types.py`**: Query classification, execution planning
- **`response_formatter.py`**: Response formatting, error handling

### Agent Modules (`src/sports_bot/agents/`)

- **`debate_agent.py`**: LLM-powered debate generation
- **`debate_integration.py`**: Integration between query system and debates

### Configuration (`src/sports_bot/config/`)

- **`api_config.py`**: API endpoints, headers, sport configurations

### Utilities (`src/sports_bot/utils/`)

- **`agent_client.py`**: Agent client utilities and helpers

## 🚀 Usage

### Running the Bot
```bash
python main.py
```

### Running Tests
```bash
# Comprehensive test suite
python tests/test_phase1_comprehensive.py

# Enhanced processing tests
python tests/test_enhanced_processing.py

# Basic architecture tests
python tests/test_phase1.py
```

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env  # Edit with your API keys
```

## 📦 Package Structure

All modules are properly organized as Python packages with `__init__.py` files:

- `src/` - Top-level source package
- `src/sports_bot/` - Main application package
- `src/sports_bot/core/` - Core functionality package
- `src/sports_bot/agents/` - AI agents package
- `src/sports_bot/config/` - Configuration package
- `src/sports_bot/utils/` - Utilities package
- `tests/` - Test package

## 🔄 Import Patterns

### Relative Imports (within package)
```python
from .stat_retriever import StatRetrieverApiAgent
from ..config.api_config import api_config
```

### Absolute Imports (from external)
```python
from sports_bot.core.sports_agents import main
from sports_bot.core.query_types import QueryType
```

## 🧹 Clean Practices

- ✅ No system files (`.DS_Store`, `__pycache__`)
- ✅ API cache files organized in `data/cache/`
- ✅ Comprehensive `.gitignore` patterns
- ✅ Proper Python package structure
- ✅ Clear separation of concerns
- ✅ All tests passing

## 🔮 Future Expansion

The structure supports easy addition of:

- New sports (add to `config/`)
- New agent types (add to `agents/`)
- New query types (extend `core/query_types.py`)
- New data sources (extend `core/stat_retriever.py`)
- New response formats (extend `core/response_formatter.py`) 