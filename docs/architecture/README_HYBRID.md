# Hybrid Sports Bot Architecture - LangChain/LangGraph + Custom Logic

This document describes the implementation of the hybrid architecture that combines LangChain/LangGraph frameworks with the existing custom sports bot logic, based on the architectural review recommendations in `docs/LangChain.md`.

## 🎯 Architecture Overview

The hybrid implementation provides the best of both worlds:

- **LangGraph Workflows**: For complex multi-agent analysis (league leaders, player debates)
- **LangChain Tools**: For standardized API integration and NLU capabilities  
- **Custom Logic Preservation**: For optimized performance where existing code excels
- **Sport Registry System**: For easy scalability to new sports

## 📁 Project Structure

```
src/sports_bot/langchain_integration/
├── __init__.py                 # Module initialization
├── tools.py                    # LangChain tools for API integration
├── workflows.py                # LangGraph workflows for complex analysis
├── sport_registry.py           # Sport configuration and adapter system
└── hybrid_agent.py             # Main hybrid agent orchestrator

hybrid_main.py                  # Interactive demo of hybrid system
```

## 🚀 Quick Start

### 1. Install Dependencies

First, install the additional LangChain dependencies:

```bash
cd ai-sports-bot-nfl
pip install langchain langchain-openai langgraph langchain-community
```

### 2. Set Environment Variables

Make sure you have your API keys configured:

```bash
# In your .env file
OPENAI_API_KEY=your_openai_api_key
RAPIDAPI_KEY=your_rapidapi_key
```

### 3. Run the Hybrid Demo

```bash
python hybrid_main.py
```

Or run in batch mode to see automated examples:

```bash
python hybrid_main.py --batch
```

## 🏗️ Component Architecture

### 1. Sport Registry System (`sport_registry.py`)

**Purpose**: Provides a scalable system for managing multiple sports with consistent interfaces.

**Key Features**:
- `SportConfiguration`: Encapsulates sport-specific settings, API endpoints, positions
- `SportAdapter`: Protocol for sport-specific logic (position stats, formatting)
- `SportRegistry`: Central registry for managing all sports

**Example - Adding a New Sport**:
```python
from sports_bot.langchain_integration.sport_registry import register_new_sport

# Add MLB support
mlb_config = {
    "sport_code": "MLB",
    "display_name": "Major League Baseball",
    "api_config": {...},
    "positions": {"pitcher": "P", "catcher": "C", ...},
    "stat_categories": {"batting": [...], "pitching": [...]},
    # ... other config
}

register_new_sport("MLB", mlb_config)
```

### 2. LangChain Tools (`tools.py`)

**Purpose**: Standardizes API integration using LangChain's tools framework.

**Available Tools**:
- `FetchPlayerStatsTool`: Get comprehensive player statistics
- `FetchTeamListingTool`: Get team information for any sport
- `FuzzyPlayerSearchTool`: Handle player name disambiguation
- `PositionNormalizationTool`: Standardize position names across sports

**Example Usage**:
```python
from sports_bot.langchain_integration.tools import FetchPlayerStatsTool, SportContext

tool = FetchPlayerStatsTool()
result = tool._run(
    player_name="Patrick Mahomes",
    sport_context=SportContext(sport="NFL", season="2024"),
    metrics=["passing_yards", "touchdowns"]
)
```

### 3. LangGraph Workflows (`workflows.py`)

**Purpose**: Implements complex multi-agent workflows for sophisticated analysis.

**Available Workflows**:

#### League Leaders Workflow
```
Extract Query → Fetch Teams → Fetch Player Data → Aggregate Stats → Format Response
```

#### Player Debate Workflow  
```
Prepare Debate → Evidence Collection → Advocate Agent → Critic Agent → Moderator Agent
```

**Example Usage**:
```python
from sports_bot.langchain_integration.workflows import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()
result = await orchestrator.execute_query(
    query="Who leads the NFL in sacks?",
    query_type="league_leaders",
    sport="NFL"
)
```

### 4. Hybrid Agent (`hybrid_agent.py`)

**Purpose**: Main orchestrator that intelligently routes queries between different processing methods.

**Processing Methods**:
1. **LangGraph Workflows**: Complex multi-step analysis
2. **Hybrid Tools**: LangChain tools + custom logic
3. **Custom Logic**: Existing optimized implementations

**Routing Logic**:
```python
if complexity == "high" and query_type in ["league_leaders", "player_debate"]:
    # Use LangGraph workflows
elif complexity == "medium" or query_type in ["single_player", "player_comparison"]:
    # Use hybrid tools approach
else:
    # Use existing custom logic
```

## 🔄 Query Processing Flow

### 1. Query Analysis
```python
# Step 1: LangChain analyzes the query
query_analysis = await self._analyze_query(user_input, context)

# Extracts:
# - Sport (NFL, NBA, etc.)
# - Query type (single_player, league_leaders, etc.)
# - Complexity (low, medium, high)
# - Player names, metrics, season, etc.
```

### 2. Intelligent Routing
```python
# Step 2: Route based on complexity and type
if complexity == "high":
    return await self._process_with_langgraph(user_input, analysis)
elif complexity == "medium":
    return await self._process_with_hybrid_tools(user_input, analysis)
else:
    return await self._process_with_custom_logic(user_input, analysis)
```

### 3. Result Processing
```python
# Step 3: Standardized result format
{
    "success": True,
    "method": "langgraph_workflow|hybrid_tools|custom_logic",
    "query_type": "league_leaders",
    "result": {...},
    "analysis": {...}
}
```

## 📊 Query Types & Processing Methods

| Query Type | Complexity | Processing Method | Example |
|------------|------------|-------------------|---------|
| Single Player | Low-Medium | Hybrid Tools | "What are Lamar Jackson's stats?" |
| Player Comparison | Medium | Hybrid Tools | "Compare Brady vs Manning" |
| Player Debate | High | LangGraph Workflow | "Who's better: LeBron or Jordan?" |
| League Leaders | High | LangGraph Workflow | "Who leads the NFL in sacks?" |
| Team Analysis | Medium | Hybrid Tools | "Show me Cowboys roster" |
| Historical Trends | Medium-High | Custom Logic | "Best QBs of the 2010s" |

## 🎮 Interactive Demo Features

The `hybrid_main.py` provides a rich interactive experience:

### System Commands
- `help` - Show example queries
- `capabilities` - Display detailed capabilities  
- `sports` - List supported sports
- `quit` - Exit the demo

### Example Queries
```bash
# NFL Examples
"Who leads the NFL in passing yards?"
"Compare Patrick Mahomes vs Josh Allen"
"What are Aaron Donald's defensive stats?"

# NBA Examples  
"Who is the leading scorer in the NBA?"
"Compare LeBron James and Stephen Curry"
"Show me Lakers roster information"
```

### Dynamic Sport Addition Demo
The demo automatically shows how to add NHL support:
```python
nhl_config = {
    "sport_code": "NHL",
    "display_name": "National Hockey League",
    # ... configuration
}
await agent.add_new_sport(nhl_config)
```

## 🔧 Configuration & Customization

### Adding a New Sport

1. **Create Sport Configuration**:
```python
sport_config = {
    "sport_code": "YOUR_SPORT",
    "display_name": "Your Sport League",
    "api_config": {
        "base_url": "https://api.yoursport.com",
        "endpoints": {...}
    },
    "positions": {...},
    "stat_categories": {...},
    # ... other settings
}
```

2. **Optional: Create Custom Adapter**:
```python
class YourSportAdapter(BaseSportAdapter):
    def get_primary_stats(self, position: str) -> List[str]:
        # Return position-specific stats
        pass
    
    def format_stat_display(self, stat_name: str, value: Any) -> str:
        # Custom formatting logic
        pass
```

3. **Register the Sport**:
```python
register_new_sport("YOUR_SPORT", sport_config, YourSportAdapter)
```

### Customizing Workflows

Add new LangGraph workflows by extending the `WorkflowOrchestrator`:

```python
class CustomWorkflow:
    def __init__(self):
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(WorkflowState)
        # Add your nodes and edges
        return workflow.compile()
```

### Adding New Tools

Create new LangChain tools by extending `BaseTool`:

```python
class CustomStatsTool(BaseTool):
    name = "custom_stats"
    description = "Description of what this tool does"
    
    def _run(self, input_param: str) -> Dict[str, Any]:
        # Your tool logic here
        pass
```

## 🔍 Monitoring & Debugging

### Query Analysis Visibility
The system provides detailed analysis of each query:
```python
{
    "sport": "NFL",
    "query_type": "single_player", 
    "complexity": "medium",
    "player_names": ["Patrick Mahomes"],
    "metrics": ["passing_yards", "touchdowns"],
    "confidence": 0.95
}
```

### Processing Method Tracking
Each result shows which method was used:
```python
{
    "method": "hybrid_tools",  # or "langgraph_workflow", "custom_logic"
    "query_type": "single_player",
    "result": {...}
}
```

### Error Handling & Fallbacks
The system includes graceful fallbacks:
- LangGraph fails → Try hybrid tools
- Hybrid tools fail → Try custom logic
- All fail → Return informative error

## 🚀 Performance Benefits

### Strategic Framework Usage
- **LangGraph**: Only for complex workflows that benefit from multi-agent orchestration
- **LangChain Tools**: For standardized API patterns while preserving custom optimizations
- **Custom Logic**: Preserved for simple, high-performance operations

### Caching Integration
All approaches leverage the existing cache system:
```python
# Tools automatically use cache
self.cache = get_cache_instance()
cached_result = self.cache.get_player_stats(player_id)
```

### Scalability Features
- **Sport Registry**: O(1) sport lookup and validation
- **Async Processing**: All workflows support async operations
- **Session Management**: Multiple concurrent user sessions

## 🧪 Testing & Validation

### Running Tests
```bash
# Test the hybrid system
python -m pytest src/sports_bot/tests/test_hybrid_integration.py

# Test individual components
python -m pytest src/sports_bot/tests/test_sport_registry.py
python -m pytest src/sports_bot/tests/test_langchain_tools.py
```

### Validation Queries
The system includes built-in validation:
```python
validation = sport_registry.validate_sport_query("NFL", {
    "season": "2024",
    "positions": ["QB", "RB"]
})
```

## 📈 Future Enhancements

### Planned Features
1. **LangSmith Integration**: Advanced monitoring and debugging
2. **Human-in-the-Loop**: Manual review for critical decisions
3. **Multi-Modal Support**: Image and video analysis
4. **Real-time Streaming**: Live game analysis
5. **Advanced RAG**: Enhanced context retrieval

### Extension Points
- **Custom Workflows**: Add domain-specific analysis patterns
- **Tool Ecosystem**: Integrate with external sports APIs
- **Adapter Patterns**: Support for new data sources
- **Query Optimization**: ML-based query routing

## 🤝 Contributing

### Adding New Sports
1. Create sport configuration following the template
2. Implement sport-specific adapter if needed
3. Add tests for the new sport
4. Update documentation

### Workflow Development
1. Design the workflow state and nodes
2. Implement using LangGraph patterns
3. Add to the WorkflowOrchestrator
4. Create comprehensive tests

### Tool Development
1. Extend BaseTool with your functionality
2. Add proper input validation and error handling
3. Include in the SPORTS_TOOLS registry
4. Document usage examples

---

This hybrid architecture successfully bridges the gap between framework convenience and custom optimization, providing a scalable foundation for multi-sport analysis while preserving the performance benefits of existing custom logic. 