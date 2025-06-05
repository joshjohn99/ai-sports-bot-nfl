# 🏈 AI Sports Bot NFL - Beta

An intelligent conversational AI system for NFL sports statistics, player analysis, and dynamic debate generation. This bot transforms natural language questions into structured API queries and provides comprehensive, contextual responses about NFL players, teams, and statistics.

## 🎯 Overview

The AI Sports Bot NFL leverages advanced natural language understanding and multi-agent architecture to provide:

- **Intelligent Query Processing**: Convert complex sports questions into structured data requests
- **Real-time NFL Statistics**: Access comprehensive player and team statistics through RapidAPI
- **Dynamic Player Comparisons**: Generate engaging debate-style comparisons between players
- **Smart Disambiguation**: Handle ambiguous player names with intelligent clarification
- **Multi-dimensional Analysis**: Support for complex queries spanning multiple players, teams, and seasons

## 🏗️ Architecture

### Core Components

#### 1. **Multi-Agent System** (`sports_agents.py`)
The orchestration layer that coordinates between specialized agents:

```
User Query → NLU Agent → Query Planner → Data Retrieval → Response Formatting
```

- **NLU Agent**: Parses natural language and extracts sports entities
- **Query Planner**: Enriches queries with execution strategies and data source planning
- **Stat Retriever**: Interfaces with NFL APIs to fetch real-time data
- **Response Formatter**: Generates contextual, user-friendly responses

#### 2. **Natural Language Understanding** (`query_types.py`)
Advanced query classification and processing:

- **QueryType Enumeration**: Single player stats, comparisons, team queries, etc.
- **QueryClassifier**: Intelligent routing based on query complexity
- **QueryExecutor**: Handles specialized execution patterns
- **Edge Case Handler**: Manages ambiguous or complex scenarios

#### 3. **API Integration Layer** (`stat_retriever.py`)
Robust interface to NFL data sources:

- **Intelligent Player Resolution**: Handles name disambiguation across teams
- **Dynamic Endpoint Selection**: Routes queries to appropriate API endpoints
- **Comprehensive Stats Schema**: Standardized mapping of NFL statistics
- **Error Handling & Validation**: Graceful handling of API limitations

#### 4. **Debate Engine** (`debate_agent.py`, `debate_integration.py`)
AI-powered player comparison system:

- **Dynamic Debate Generation**: Creates engaging player vs. player arguments
- **Evidence-based Analysis**: Uses real statistics to support arguments
- **Multiple Debate Styles**: Supports various comparison frameworks

#### 5. **Configuration Management** (`api_config.py`)
Centralized API configuration with support for:

- RapidAPI NFL endpoints
- Authentication management
- Endpoint routing and parameter handling

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- RapidAPI account with NFL API access
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/joshjohn99/ai-sports-bot-nfl.git
   cd ai-sports-bot-nfl/sports_bot_beta
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   RAPIDAPI_KEY=your_rapidapi_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Verify installation**
   ```bash
   python test_phase1.py
   ```

### API Setup

#### RapidAPI Configuration
1. Sign up at [RapidAPI](https://rapidapi.com/)
2. Subscribe to the [NFL API Data](https://rapidapi.com/api-sports/api/nfl-api-data) service
3. Copy your API key to the `.env` file

#### OpenAI Setup
1. Create an account at [OpenAI](https://platform.openai.com/)
2. Generate an API key
3. Add the key to your `.env` file

## 📋 Usage Examples

### Basic Player Statistics
```python
from sports_agents import run_query_planner

# Get player statistics
result = await run_query_planner("How many touchdowns did Josh Allen throw in 2023?")
```

### Team Information
```python
# Count teams in the league
result = await run_query_planner("How many teams are in the NFL?")
```

### Player Comparisons
```python
# Compare players with debate-style analysis
result = await run_query_planner("Who is better, Josh Allen or Patrick Mahomes?")
```

### Complex Queries
```python
# Multi-dimensional analysis
result = await run_query_planner("Which quarterback had the most passing yards in clutch situations during the 2023 playoffs?")
```

## 🛠️ Key Features

### Intelligent Query Processing
- **Natural Language Understanding**: Converts conversational queries into structured data requests
- **Context Awareness**: Maintains conversation context for follow-up questions
- **Ambiguity Resolution**: Smart handling of common player name conflicts

### Comprehensive NFL Data Access
- **Real-time Statistics**: Current season and historical data
- **Player Information**: Detailed player profiles, positions, and team affiliations
- **Team Data**: Complete team rosters and organizational information
- **Advanced Metrics**: Support for complex statistical calculations

### Enhanced User Experience
- **Conversational Interface**: Natural language input and contextual responses
- **Error Recovery**: Graceful handling of invalid or incomplete queries
- **Progressive Disclosure**: Guided clarification for ambiguous requests

## 🧪 Testing

The project includes comprehensive testing suites:

- **Unit Tests**: `test_phase1.py` - Core functionality validation
- **Integration Tests**: `test_phase1_comprehensive.py` - End-to-end workflow testing
- **Enhanced Processing Tests**: `test_enhanced_processing.py` - Advanced feature validation

Run tests:
```bash
python test_phase1_comprehensive.py
```

## 📊 Sample Data

The `sampledata/` directory contains example API responses for development and testing:
- `resp.json` - Sample player statistics response
- `teamreps.json` - Sample team roster data

## 🔮 Future Development Plans

### Phase 2: Multi-Sport Expansion
- **NBA Integration**: Basketball statistics and player comparisons
- **MLB Support**: Baseball metrics and historical data
- **NHL Coverage**: Hockey statistics and team analysis
- **Cross-Sport Comparisons**: Normalized metrics across different sports

### Phase 3: Advanced Analytics
- **Predictive Modeling**: AI-powered performance predictions
- **Trend Analysis**: Historical pattern recognition and forecasting
- **Advanced Visualizations**: Interactive charts and statistical dashboards
- **Real-time Game Integration**: Live game statistics and play-by-play analysis

### Phase 4: Enhanced User Experience
- **Web Interface**: React-based frontend application
- **Mobile App**: Native iOS and Android applications
- **Voice Integration**: Alexa and Google Assistant compatibility
- **Social Features**: Shareable debates and community discussions

### Phase 5: Enterprise Features
- **Fantasy Sports Integration**: Draft recommendations and lineup optimization
- **Betting Insights**: Statistical analysis for informed decision-making
- **Team Management Tools**: Professional scouting and analysis features
- **API Marketplace**: Third-party integrations and custom endpoints

## 🤝 Contributing

We welcome contributions to improve the AI Sports Bot! Please see our contributing guidelines for:

- Code standards and best practices
- Testing requirements
- Documentation expectations
- Pull request processes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **RapidAPI**: For providing comprehensive NFL data access
- **OpenAI**: For powering the natural language understanding capabilities
- **ESPN API**: For supplementary sports data
- **NFL**: For official statistics and data standards

## 📞 Support

For questions, issues, or feature requests:

- **GitHub Issues**: Submit bug reports and feature requests
- **Documentation**: Comprehensive guides and API references
- **Community**: Join our Discord server for real-time support

---

**Built with ❤️ for sports fans and data enthusiasts** 