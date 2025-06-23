# 🌟 Universal Sports Agent - Multi-Sport Intelligence System

## Overview

The Universal Sports Agent is an advanced, dynamic multi-sport traffic director that intelligently routes queries between different sports systems (NFL, NBA, MLB, NHL, MLS, NASCAR, F1, and more). Built with LangChain and LangGraph, it provides seamless conversation flow and can be extended to support any sport without code changes.

## 🚀 Key Features

### 🎯 Intelligent Sport Detection
- **Dynamic Recognition**: Automatically detects which sport(s) a query involves
- **Multi-Sport Queries**: Handles cross-sport comparisons and analysis
- **Confidence Scoring**: Provides confidence levels for sport detection
- **Context Awareness**: Maintains conversation context for follow-up questions

### 🔀 Smart Query Routing
- **Single Sport**: Routes to appropriate sport-specific systems
- **Cross-Sport**: Handles multi-sport comparisons intelligently
- **Fallback Handling**: Graceful degradation when systems are unavailable
- **Error Recovery**: Intelligent error handling with helpful suggestions

### 🌐 Dynamic Sport Support
- **Extensible Registry**: Add new sports without code changes
- **Auto-Discovery**: Automatically discovers available sport databases
- **Pattern Learning**: Learns sport-specific patterns and terminology
- **Real-time Addition**: Add sports during runtime

### 🧠 Advanced Processing
- **LangChain Integration**: Uses LangChain for intelligent reasoning
- **LangGraph Workflows**: Complex multi-step query processing
- **Conversation Memory**: Maintains context across interactions
- **Performance Monitoring**: Tracks usage and performance metrics

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Universal Sports Agent                    │
├─────────────────────────────────────────────────────────────┤
│  🎯 Sport Detection    │  🔀 Query Routing  │  🧠 Processing │
│  • Pattern Matching   │  • Single Sport    │  • LangChain   │
│  • Entity Extraction  │  • Cross-Sport     │  • LangGraph   │
│  • Confidence Scoring │  • Fallback        │  • Memory      │
├─────────────────────────────────────────────────────────────┤
│                    Unified Sports Interface                  │
├─────────────────────────────────────────────────────────────┤
│  🏈 NFL System  │  🏀 NBA System  │  ⚾ MLB System  │  🏒 NHL │
│  • 2,920+ players │  • 407 cached   │  • Auto-config  │  • ... │
│  • LangChain ready│  • LangGraph    │  • Dynamic      │       │
├─────────────────────────────────────────────────────────────┤
│                    Sport Registry (Dynamic)                  │
│  🏁 NASCAR  │  🏎️ F1  │  ⚽ MLS  │  🎾 Tennis  │  🏏 Cricket │
└─────────────────────────────────────────────────────────────┘
```

## 🎮 Usage Examples

### Basic Sports Queries
```python
# NFL Query
response = await query_sports("NFL quarterback stats for Tom Brady")

# NBA Query  
response = await query_sports("NBA player LeBron James career points")

# Cross-Sport Comparison
response = await query_sports("Compare NFL and NBA player salaries")
```

### Adding New Sports
```python
# Add Tennis support
add_sport(
    "Tennis",
    keywords=["tennis", "serve", "ace", "set", "match", "wimbledon"],
    stats=["aces", "double faults", "first serve percentage", "winners"],
    positions=["singles", "doubles"]
)

# Now tennis queries work automatically
response = await query_sports("Tennis player Novak Djokovic Grand Slam wins")
```

### Interactive Mode
```bash
# Start the Universal Sports Bot
python main.py

# Available commands:
# - Ask about any sport: "NFL stats for Patrick Mahomes"
# - Show dashboard: "dashboard"  
# - Show supported sports: "sports"
# - Add new sport: "add sport"
# - Test all systems: "test"
```

## 🔧 Installation & Setup

### Prerequisites
```bash
# Install required dependencies
pip install langchain langgraph openai rich
```

### Quick Start
```python
import asyncio
from sports_bot.agents.agent_integration import query_sports

# Simple query
async def main():
    response = await query_sports("NFL quarterback stats")
    print(response)

asyncio.run(main())
```

### Command Line Usage
```bash
# Interactive mode with Universal Agent
python main.py

# Show performance dashboard
python main.py --dashboard

# Show supported sports
python main.py --sports

# Test all sports systems
python main.py --test

# Run NFL LangChain upgrade
python main.py --upgrade-nfl
```

## 📊 Supported Sports

### Currently Active
| Sport | Status | Players | Features |
|-------|--------|---------|----------|
| 🏈 NFL | ✅ Active | 2,920+ | Full LangChain integration |
| 🏀 NBA | ✅ Active | 407 cached | LangGraph workflows |
| ⚾ MLB | 🔄 Configured | Auto-discovery | Pattern recognition |
| 🏒 NHL | 🔄 Configured | Auto-discovery | Pattern recognition |
| ⚽ MLS | 🔄 Configured | Auto-discovery | Pattern recognition |
| 🏁 NASCAR | 🔄 Configured | Auto-discovery | Pattern recognition |
| 🏎️ F1 | 🔄 Configured | Auto-discovery | Pattern recognition |

### Easy to Add
- 🎾 Tennis
- 🏏 Cricket  
- 🏐 Volleyball
- 🏓 Table Tennis
- 🏸 Badminton
- 🥊 Boxing
- 🥋 MMA
- ⛳ Golf
- 🎿 Skiing
- 🏊 Swimming
- And any other sport!

## 🧪 Testing

### Run Demo
```bash
# Full Universal Agent demo
python test_universal_agent.py

# Basic functionality test
python test_universal_agent.py --basic
```

### Test Queries
```python
test_queries = [
    "NFL quarterback Tom Brady stats",
    "NBA player LeBron James points",
    "Compare NFL and NBA performance",
    "Who is the best athlete?",
    "Tennis player rankings"  # Triggers sport addition
]
```

## 📈 Performance Monitoring

### Built-in Dashboard
```python
# Show performance metrics
show_dashboard()

# Get performance stats
stats = get_sports_stats()
print(f"Success Rate: {stats['success_rate']:.1f}%")
print(f"Average Response Time: {stats['average_response_time']:.2f}s")
```

### Metrics Tracked
- Query success/failure rates
- Response times per sport
- Sport detection confidence
- System availability status
- User interaction patterns

## 🔌 Integration Points

### With Existing Systems
```python
# NFL System Integration
from sports_bot.agents.sports_agents import run_query_planner

# NBA System Integration  
from sports_bot.cache.shared_cache import sports_cache

# Database Integration
from sports_bot.database.sport_models import sport_db_manager
```

### API Integration
```python
# RESTful API wrapper (future)
@app.route('/query', methods=['POST'])
async def api_query():
    query = request.json['query']
    response = await query_sports(query)
    return {'response': response}
```

## 🎛️ Configuration

### Sport Registry Configuration
```python
# Custom sport patterns
sport_patterns = {
    "keywords": ["custom", "sport", "terms"],
    "teams": ["team1", "team2"],
    "stats": ["stat1", "stat2"],
    "positions": ["pos1", "pos2"]
}

universal_agent.add_sport_to_registry("CustomSport", sport_patterns)
```

### LLM Configuration
```python
# Configure different LLMs
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# OpenAI GPT-4
llm = ChatOpenAI(model="gpt-4", temperature=0.1)

# Anthropic Claude
llm = ChatAnthropic(model="claude-3-sonnet-20240229")
```

## 🚨 Error Handling

### Graceful Degradation
- **Universal Agent Unavailable**: Falls back to legacy NFL system
- **LangChain Missing**: Uses simplified pattern matching
- **Database Issues**: Provides helpful error messages
- **API Failures**: Intelligent retry and fallback mechanisms

### Error Recovery
```python
try:
    response = await query_sports("complex query")
except Exception as e:
    # Automatic fallback to simpler processing
    response = fallback_processor(query)
```

## 🔮 Future Enhancements

### Planned Features
- **Voice Interface**: Speech-to-text query processing
- **Visual Analytics**: Chart and graph generation
- **Real-time Data**: Live sports data integration  
- **Multi-language**: Support for multiple languages
- **Mobile App**: Native mobile applications
- **API Gateway**: RESTful API for external integrations

### Advanced Capabilities
- **Predictive Analytics**: Future performance predictions
- **Sentiment Analysis**: Fan sentiment and opinion analysis
- **Social Media Integration**: Twitter, Reddit sports discussions
- **Fantasy Sports**: Fantasy league management and advice
- **Betting Insights**: Statistical analysis for sports betting

## 🤝 Contributing

### Adding New Sports
1. **Define Patterns**: Create keyword, team, stat, and position patterns
2. **Test Detection**: Verify sport detection works correctly
3. **Add Data Source**: Connect to sport-specific data APIs/databases
4. **Document**: Update documentation with new sport info

### Code Contributions
1. **Fork Repository**: Create your feature branch
2. **Implement Changes**: Follow existing code patterns
3. **Add Tests**: Include comprehensive tests
4. **Submit PR**: Provide detailed description of changes

## 📚 API Reference

### Core Functions
```python
# Main query function
await query_sports(query: str, user_id: str = None, conversation_id: str = None) -> str

# Add new sport
add_sport(sport: str, keywords: List[str], teams: List[str] = None, 
          stats: List[str] = None, positions: List[str] = None)

# Get supported sports
get_supported_sports() -> List[str]

# Performance stats
get_sports_stats() -> Dict[str, Any]

# Show dashboard
show_dashboard()
```

### Advanced Usage
```python
# Direct Universal Agent access
from sports_bot.agents.universal_sports_agent import universal_sports_agent

# Process with custom context
result = await universal_sports_agent.process_query(
    query="NFL stats", 
    user_id="user123", 
    conversation_id="session456"
)

# Get conversation history
history = universal_sports_agent.get_conversation_history()

# Reset conversation
universal_sports_agent.reset_conversation()
```

## 📞 Support

### Getting Help
- **Documentation**: Check this README and inline code docs
- **Issues**: Create GitHub issues for bugs or feature requests
- **Discussions**: Use GitHub discussions for questions
- **Examples**: Check `test_universal_agent.py` for usage examples

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed
2. **Database Connection**: Verify database files exist and are accessible
3. **LangChain Issues**: Check API keys and model availability
4. **Performance**: Monitor memory usage with large datasets

---

## 🎉 Conclusion

The Universal Sports Agent represents a major leap forward in sports data intelligence, providing:

- **🎯 Intelligent Routing**: Automatic sport detection and query routing
- **🌐 Universal Support**: Any sport can be added dynamically  
- **🧠 Advanced Processing**: LangChain/LangGraph powered intelligence
- **📈 Performance Monitoring**: Built-in analytics and dashboards
- **🔧 Easy Integration**: Simple APIs and extensive documentation

Whether you're building a sports app, analyzing player performance, or just curious about sports statistics, the Universal Sports Agent provides the intelligent foundation you need.

**Ready to revolutionize sports data interaction? Start with a simple query and watch the magic happen! 🌟** 