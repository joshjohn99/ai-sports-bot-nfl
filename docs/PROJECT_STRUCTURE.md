# Project Structure

This document outlines the organization and structure of the AI Sports Bot NFL project.

## 📁 Directory Overview

```
ai-sports-bot-nfl/
├── .github/                    # GitHub-specific files
│   └── workflows/             # GitHub Actions CI/CD workflows
│       └── ci.yml            # Continuous Integration pipeline
├── docs/                      # Documentation
│   ├── analysis/             # Technical analysis documents
│   │   ├── API_EFFICIENCY_ANALYSIS.md
│   │   ├── CACHE_SOLUTION_SUMMARY.md
│   │   └── CACHE_STRATEGY.md
│   ├── architecture/         # Architecture documentation
│   │   ├── AGENT_INTEGRATION_SUMMARY.md
│   │   ├── README_HYBRID.md
│   │   └── SCALABLE_COMPARISON_ARCHITECTURE.md
│   ├── LangChain.md         # LangChain integration guide
│   ├── STRUCTURE.md         # Legacy structure documentation
│   └── PROJECT_STRUCTURE.md # This file
├── examples/                  # Example scripts and demos
│   ├── analyze_available_endpoints.py
│   ├── bridge_demo.py
│   ├── debug_touchdowns.py
│   └── hybrid_main.py
├── scripts/                   # Utility scripts
│   ├── fetch_sample_data.py
│   └── init_database.py
├── src/                       # Source code
│   ├── agent_framework.py    # Custom agent framework
│   └── sports_bot/           # Main package
│       ├── agents/           # AI agents
│       ├── api/              # API client and schemas
│       ├── cache/            # Caching system
│       ├── config/           # Configuration files
│       ├── core/             # Core functionality
│       ├── data/             # Data models and operations
│       ├── db/               # Database operations
│       ├── langchain_integration/  # LangChain/LangGraph integration
│       ├── query/            # Query processing
│       ├── stats/            # Statistics handling
│       ├── tests/            # Package-specific tests
│       └── utils/            # Utility functions
├── tests/                     # Test suite
│   ├── test_enhanced_processing.py
│   ├── test_phase1.py
│   └── test_phase1_comprehensive.py
├── data/                      # Data storage
│   └── samples/              # Sample API responses
├── config/                    # Configuration files
│   └── api_config.py
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
├── .pre-commit-config.yaml  # Pre-commit hooks configuration
├── CONTRIBUTING.md          # Contribution guidelines
├── LICENSE                  # MIT License
├── README.md               # Main project documentation
├── main.py                 # Main entry point
├── pyproject.toml          # Modern Python project configuration
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── run.sh                  # Shell script runner
├── setup.py               # Legacy setup configuration
└── test_integration_final.py  # Final integration test
```

## 🏗️ Core Architecture

### Source Code Organization (`src/sports_bot/`)

#### 1. **Agents** (`agents/`)
- **Purpose**: AI agent implementations
- **Key Files**:
  - `sports_agents.py` - Custom NLU and query planning agents
  - `sports_commentary_agent.py` - Commentary generation agent
  - `debate_agent.py` - Player comparison debate agent
  - `debate_integration.py` - Debate system integration

#### 2. **API** (`api/`)
- **Purpose**: External API integration
- **Key Files**:
  - `client.py` - HTTP client for sports APIs
  - `endpoints.py` - API endpoint definitions
  - `schemas.py` - Pydantic models for API responses
  - `test_api_connection.py` - API connectivity tests

#### 3. **Cache** (`cache/`)
- **Purpose**: Performance optimization through caching
- **Key Files**:
  - `shared_cache.py` - Multi-user caching system

#### 4. **Configuration** (`config/`)
- **Purpose**: Application configuration management
- **Key Files**:
  - `api_config.py` - API keys and endpoints
  - `db_config.py` - Database configuration

#### 5. **Core** (`core/`)
- **Purpose**: Core business logic
- **Subdirectories**:
  - `agents/` - Core agent interfaces
  - `query/` - Query type definitions
  - `stats/` - Statistics processing

#### 6. **Data** (`data/`)
- **Purpose**: Data models and operations
- **Key Files**:
  - `player.py` - Player data models
  - `team.py` - Team data models
  - `stats.py` - Statistics models
  - `fetcher.py` - Data fetching logic
  - `data_loader.py` - Data loading utilities

#### 7. **Database** (`db/`)
- **Purpose**: Database operations and models
- **Key Files**:
  - `models.py` - SQLAlchemy models
  - `operations.py` - Database operations
  - `connection.py` - Database connection management

#### 8. **LangChain Integration** (`langchain_integration/`)
- **Purpose**: Modern LLM framework integration
- **Key Files**:
  - `agent_bridge.py` - Bridge between custom and LangChain agents
  - `hybrid_agent.py` - Hybrid agent implementation
  - `sport_registry.py` - Multi-sport registry system
  - `tools.py` - LangChain tools
  - `workflows.py` - LangGraph workflows

#### 9. **Query Processing** (`query/`)
- **Purpose**: Query understanding and processing
- **Key Files**:
  - `query_types.py` - Query type definitions

#### 10. **Statistics** (`stats/`)
- **Purpose**: Statistics retrieval and formatting
- **Key Files**:
  - `stat_retriever.py` - Statistics retrieval logic
  - `response_formatter.py` - Response formatting

#### 11. **Utilities** (`utils/`)
- **Purpose**: Common utility functions
- **Key Files**:
  - `helpers.py` - General helper functions
  - `logging.py` - Logging configuration
  - `agent_client.py` - Agent client utilities

## 🎯 Key Design Patterns

### 1. **Hybrid Architecture**
- Combines custom agents with LangChain/LangGraph
- Intelligent routing based on query complexity
- Graceful fallbacks across systems

### 2. **Multi-Sport Registry**
- Extensible design for adding new sports
- Sport-specific configurations and adapters
- Unified interface across different sports

### 3. **Layered Caching**
- Multiple cache levels for performance
- User-specific and shared caching strategies
- TTL-based cache invalidation

### 4. **Agent Bridge Pattern**
- Unified entry point for all query processing
- Decision tree for optimal agent selection
- Performance monitoring and analytics

## 🧪 Testing Strategy

### Test Organization
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Complete workflow testing
- **Performance Tests**: API efficiency and caching tests

### Test Locations
- `tests/` - Main test suite
- `src/sports_bot/tests/` - Package-specific tests
- `test_integration_final.py` - Final integration validation

## 📚 Documentation Structure

### Technical Documentation (`docs/`)
- **Architecture**: System design and patterns
- **Analysis**: Performance and efficiency studies
- **Integration**: LangChain and external service guides

### User Documentation
- `README.md` - Main project overview
- `CONTRIBUTING.md` - Contribution guidelines
- Examples in `examples/` directory

## 🚀 Deployment and CI/CD

### GitHub Actions (`.github/workflows/`)
- **CI Pipeline**: Automated testing and quality checks
- **Security Scanning**: Dependency and code security analysis
- **Documentation**: Automated documentation building

### Development Tools
- **Pre-commit Hooks**: Code quality enforcement
- **Type Checking**: MyPy static analysis
- **Code Formatting**: Black and isort
- **Linting**: Flake8 code quality checks

## 🔧 Configuration Management

### Environment Variables
- `.env.example` - Template for required variables
- Separate configurations for development/production
- Secure API key management

### Project Configuration
- `pyproject.toml` - Modern Python project configuration
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies

## 📈 Scalability Considerations

### Horizontal Scaling
- Stateless agent design
- Database connection pooling
- Distributed caching support

### Vertical Scaling
- Efficient query processing
- Optimized API usage
- Memory-conscious caching

### Multi-Sport Expansion
- Registry-based sport management
- Pluggable sport adapters
- Unified query interface

## 🔍 Monitoring and Observability

### Logging
- Structured logging throughout the application
- Configurable log levels
- Performance metrics tracking

### Analytics
- Query routing statistics
- Agent performance metrics
- Cache hit/miss ratios
- API usage tracking

## 🛠️ Development Workflow

### Local Development
1. Clone repository
2. Set up virtual environment
3. Install dependencies
4. Configure environment variables
5. Initialize database
6. Run tests
7. Start development server

### Code Quality
- Pre-commit hooks for automatic checks
- Continuous integration on pull requests
- Code coverage requirements
- Security vulnerability scanning

This structure provides a solid foundation for a production-ready AI sports bot with room for future expansion and enhancement. 