# NFL Sports Statistics and Debate System

A comprehensive system for retrieving NFL statistics and generating intelligent debates about players and teams.

## Project Status

### Completed Features

1. Data Fetching Layer (`NFLDataFetcher`)
   - ✅ Team listing and details
   - ✅ Player roster retrieval
   - ✅ Player statistics and information
   - ✅ Rate limiting and caching
   - ✅ Error handling and retries
   - ✅ Response validation

2. Debate Agent (`DebateAgent`)
   - ✅ Player statistics lookup
   - ✅ Multi-player comparisons
   - ✅ Team context search
   - ✅ Basic debate generation
   - ✅ Comprehensive test coverage

### Next Steps

1. Enhanced Statistics Analysis
   - [ ] Historical performance tracking
   - [ ] Advanced player metrics
   - [ ] Team performance trends
   - [ ] Position-specific statistics

2. Natural Language Processing
   - [ ] Generate narrative insights
   - [ ] Context-aware comparisons
   - [ ] Statistical significance analysis
   - [ ] Performance prediction

3. User Interface
   - [ ] CLI for quick queries
   - [ ] Web interface for visualizations
   - [ ] API documentation
   - [ ] Interactive debate mode

4. Data Management
   - [ ] Local caching system
   - [ ] Database integration
   - [ ] Regular data updates
   - [ ] Historical data storage

## Getting Started

### Prerequisites

- Python 3.8+
- RapidAPI account with NFL API access

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-sports-bot-nfl
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export RAPIDAPI_KEY=your_api_key_here
```

### Running Tests

```bash
PYTHONPATH=. pytest tests/ -v
```

## Project Structure

```
ai-sports-bot-nfl/
├── src/
│   └── sports_bot/
│       ├── agents/
│       │   └── debate_agent.py      # Main debate agent implementation
│       └── data/
│           ├── fetcher.py           # NFL data fetching
│           └── response_formatter.py # Response formatting utilities
├── tests/
│   └── test_debate_agent.py         # Comprehensive test suite
└── README.md                        # This file
```

## API Usage

### Basic Example

```python
from sports_bot.agents.debate_agent import DebateAgent, DebateContext

async with DebateAgent(api_key="your_api_key") as agent:
    # Compare two players
    debate = await agent.generate_debate(DebateContext(
        query="Compare Kyler Murray and Josh Allen's passing performance",
        player_names=["Kyler Murray", "Josh Allen"],
        metrics=["completions", "passingYards", "passingTouchdowns"]
    ))
```

### Player Lookup Example

```python
from sports_bot.data.fetcher import NFLDataFetcher
from sports_bot.data.response_formatter import ResponseFormatter
from sports_bot.data.player_lookup import PlayerLookup

fetcher = NFLDataFetcher(api_key="your_api_key")
formatter = ResponseFormatter()
lookup = PlayerLookup(fetcher, formatter)

# Simple one-off call (context handled internally)
player = await lookup.lookup_player_stats("Kyler Murray")

# For multiple requests reuse the fetcher context
async with fetcher:
    comparison = await lookup.compare_players("Kyler Murray", "Josh Allen")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 