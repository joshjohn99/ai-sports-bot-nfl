# 🏈 AI Sports Bot NFL - Hybrid Architecture

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![LangChain](https://img.shields.io/badge/LangChain-Framework-green.svg)](https://langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com/)

An intelligent conversational AI system for NFL sports statistics, player analysis, and dynamic debate generation. This bot combines custom-built agents with modern LLM frameworks (LangChain/LangGraph) to provide comprehensive, contextual responses about NFL players, teams, and statistics.

## 🎯 Features

- **🤖 Hybrid AI Architecture**: Combines custom agents with LangChain/LangGraph for optimal performance
- **📊 Real-time NFL Statistics**: Access comprehensive player and team statistics through RapidAPI
- **🥊 Dynamic Player Debates**: AI-powered comparison system with multi-agent debate engine
- **🔍 Smart Player Disambiguation**: Intelligent handling of ambiguous player names
- **⚡ Intelligent Query Routing**: Automatic selection of optimal processing method
- **🏆 League Leaders Analysis**: Complex multi-agent workflows for ranking queries
- **💾 Shared Caching System**: Prevents API explosion with efficient multi-user caching
- **🎯 Scalable Comparisons**: Support for n-way player, team, and season comparisons

## 🏗️ Architecture

### Hybrid System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Bridge                             │
│              (Intelligent Routing)                         │
├─────────────────────────────────────────────────────────────┤
│  Custom NLU    │  LangGraph      │  LangChain    │  Custom  │
│  Agents        │  Workflows      │  Tools        │  Logic   │
│                │                 │               │          │
│  • Query       │  • League       │  • API        │  • Stat  │
│    Planning    │    Leaders      │    Integration│    Retrieval│
│  • Entity      │  • Player       │  • Sport      │  • Caching│
│    Extraction  │    Debates      │    Registry   │  • Formatting│
└─────────────────────────────────────────────────────────────┘
```

### Core Components

- **Agent Bridge**: Central orchestrator with intelligent routing
- **Custom NLU Agents**: Proven query understanding and planning
- **LangGraph Workflows**: Complex multi-agent analysis for debates and rankings
- **LangChain Tools**: Standardized API operations and sport management
- **Shared Cache System**: Efficient multi-user data management

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- RapidAPI account with NFL API access
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ai-sports-bot/ai-sports-bot-nfl.git
   cd ai-sports-bot-nfl
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # RAPIDAPI_KEY=your_rapidapi_key_here
   # OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Initialize the system**
   ```bash
   python scripts/init_database.py
   ```

### Running the Bot

#### Option 1: Hybrid Demo (Recommended)
```bash
python examples/hybrid_main.py
```

#### Option 2: Agent Bridge Demo
```bash
python examples/bridge_demo.py
```

#### Option 3: Classic Interface
```bash
python main.py
```

## 💡 Usage Examples

### Basic Player Statistics
```
🏈 Enter your sports query: What are Lamar Jackson's rushing yards?
```

### Player Comparisons
```
🏈 Enter your sports query: Compare Josh Allen and Patrick Mahomes passing stats
```

### League Leaders
```
🏈 Enter your sports query: Who leads the NFL in sacks this season?
```

### Multi-Player Analysis
```
🏈 Enter your sports query: Compare Micah Parsons, T.J. Watt, and Myles Garrett
```

## 📁 Project Structure

```
ai-sports-bot-nfl/
├── 📄 README.md                    # This file
├── 📄 requirements.txt             # Python dependencies
├── 📄 LICENSE                      # MIT License
├── 📄 .gitignore                   # Git ignore patterns
├── 📄 .env.example                 # Environment variables template
│
├── 🐍 main.py                      # Classic interface entry point
├── 🐍 hybrid_main.py               # Hybrid demo entry point
├── 🐍 bridge_demo.py               # Agent bridge demo
├── 🐍 test_integration_final.py    # Integration tests
│
├── 📁 src/                         # Source code
│   └── sports_bot/
│       ├── agents/                 # AI agents and debate engine
│       ├── api/                    # API integration layer
│       ├── cache/                  # Shared caching system
│       ├── config/                 # Configuration management
│       ├── core/                   # Core business logic
│       ├── data/                   # Data management
│       ├── db/                     # Database operations
│       ├── langchain_integration/  # LangChain/LangGraph hybrid
│       ├── stats/                  # Statistics processing
│       ├── tests/                  # Unit tests
│       └── utils/                  # Utility functions
│
├── 📁 tests/                       # Test suite
├── 📁 scripts/                     # Setup and utility scripts
├── 📁 docs/                        # Documentation
├── 📁 data/                        # Data storage and samples
└── 📁 config/                      # Configuration files
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Integration tests
python test_integration_final.py

# Unit tests
python -m pytest tests/ -v

# Specific test modules
python tests/test_phase1_comprehensive.py
```

## 🔧 Configuration

### API Setup

#### RapidAPI Configuration
1. Sign up at [RapidAPI](https://rapidapi.com/)
2. Subscribe to the [NFL API Data](https://rapidapi.com/api-sports/api/nfl-api-data) service
3. Copy your API key to the `.env` file

#### OpenAI Setup
1. Create an account at [OpenAI](https://platform.openai.com/)
2. Generate an API key
3. Add the key to your `.env` file

### Environment Variables
```bash
# Required
RAPIDAPI_KEY=your_rapidapi_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional
NFL_SEASON=2024
CACHE_TTL_HOURS=24
LOG_LEVEL=INFO
```

## 📊 Performance & Efficiency

### API Optimization
- **99% API call reduction** with shared caching
- **Intelligent player disambiguation** reduces lookup failures
- **Batch processing** for multi-player queries
- **Graceful fallbacks** ensure reliability

### Caching Strategy
- **Shared cache** across all users prevents API explosion
- **TTL policies** balance performance with data freshness
- **Thread-safe** concurrent user access
- **Statistics tracking** for performance monitoring

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v

# Run linting
flake8 src/

# Format code
black src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **RapidAPI**: For providing comprehensive NFL data access
- **OpenAI**: For powering the natural language understanding capabilities
- **LangChain/LangGraph**: For the hybrid architecture framework
- **NFL**: For official statistics and data standards

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ai-sports-bot/ai-sports-bot-nfl/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ai-sports-bot/ai-sports-bot-nfl/discussions)
- **Documentation**: [Project Wiki](https://github.com/ai-sports-bot/ai-sports-bot-nfl/wiki)

---

**Built with ❤️ for sports fans and AI enthusiasts** 