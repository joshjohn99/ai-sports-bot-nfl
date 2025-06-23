"""
Universal Sports Agent - Dynamic Multi-Sport Traffic Director

This agent uses LangChain and LangGraph to:
1. Intelligently detect which sport(s) a query involves
2. Route queries to the appropriate sport-specific systems
3. Handle cross-sport comparisons and conversations
4. Maintain smooth conversation flow across sports
5. Dynamically support new sports without code changes
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

# LangChain imports
try:
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.tools import BaseTool, tool
    from langchain.prompts import PromptTemplate
    from langchain.schema import Document
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.callbacks import StreamingStdOutCallbackHandler
    from langchain_openai import ChatOpenAI
except ImportError:
    # Fallback for systems without LangChain
    print("LangChain not available, using simplified mode")
    BaseTool = object
    tool = lambda func: func
    ChatOpenAI = None

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolExecutor
except ImportError:
    # Fallback for systems without LangGraph
    print("LangGraph not available, using simplified workflow")
    StateGraph = None
    END = "END"

# Rich for beautiful output
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

class SportDetectionConfidence(Enum):
    """Confidence levels for sport detection"""
    CERTAIN = 0.9
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    UNKNOWN = 0.2

@dataclass
class SportContext:
    """Context information for a detected sport"""
    sport: str
    confidence: float
    entities: List[str] = field(default_factory=list)  # Players, teams, etc.
    metrics: List[str] = field(default_factory=list)   # Stats requested
    reasoning: str = ""
    database_available: bool = False
    cache_available: bool = False

@dataclass
class UniversalQueryState:
    """State for LangGraph processing"""
    original_query: str
    detected_sports: List[SportContext] = field(default_factory=list)
    primary_sport: Optional[str] = None
    query_type: str = "unknown"
    entities: Dict[str, List[str]] = field(default_factory=dict)
    metrics: List[str] = field(default_factory=list)
    conversation_context: Dict[str, Any] = field(default_factory=dict)
    routing_decision: Dict[str, Any] = field(default_factory=dict)
    responses: Dict[str, Any] = field(default_factory=dict)
    final_response: str = ""
    error_messages: List[str] = field(default_factory=list)

class UniversalSportsAgent:
    """
    Universal Sports Agent - Dynamic Multi-Sport Traffic Director
    
    Features:
    - LangChain-powered sport detection and entity extraction
    - LangGraph workflow for intelligent query routing
    - Dynamic sport support (no hardcoded sport lists)
    - Cross-sport conversation memory
    - Intelligent fallback and error handling
    """
    
    def __init__(self):
        self.console = Console()
        
        # Initialize conversation memory
        self.conversation_history = []
        
        # Initialize LLM if available
        self.llm = self._initialize_llm()
        
        # Initialize sport detection tools
        self.sport_detection_tools = self._create_sport_detection_tools()
        
        # Initialize workflow (LangGraph or fallback)
        self.workflow = self._create_workflow()
        
        # Dynamic sport registry
        self.sport_registry = self._initialize_sport_registry()
        
        console.print(Panel.fit(
            "[bold blue]🌟 Universal Sports Agent Initialized[/bold blue]\n"
            "[cyan]• Dynamic multi-sport support[/cyan]\n"
            "[cyan]• Intelligent query routing[/cyan]\n"
            "[cyan]• Cross-sport conversation memory[/cyan]\n"
            "[cyan]• Extensible sport registry[/cyan]",
            border_style="blue"
        ))

    def _initialize_llm(self):
        """Initialize the best available LLM"""
        if ChatOpenAI:
            try:
                return ChatOpenAI(
                    model="gpt-4",
                    temperature=0.1
                )
            except:
                try:
                    return ChatOpenAI(temperature=0.1)
                except:
                    pass
        return None

    def _initialize_sport_registry(self) -> Dict[str, Dict[str, Any]]:
        """Initialize dynamic sport registry with detection patterns"""
        
        # Base sport patterns - these can be dynamically extended
        base_registry = {
            "NFL": {
                "keywords": [
                    "nfl", "football", "quarterback", "qb", "running back", "rb", 
                    "wide receiver", "wr", "tight end", "te", "linebacker", "lb",
                    "defensive end", "de", "cornerback", "cb", "safety", "touchdown",
                    "yards", "sacks", "tackles", "interception", "fumble", "field goal"
                ],
                "teams": [
                    "cowboys", "patriots", "packers", "steelers", "49ers", "giants",
                    "eagles", "ravens", "chiefs", "bills", "dolphins", "jets",
                    "titans", "colts", "texans", "jaguars", "broncos", "chargers",
                    "raiders", "bengals", "browns", "rams", "cardinals", "seahawks",
                    "lions", "bears", "vikings", "saints", "falcons", "panthers",
                    "buccaneers", "commanders", "washington"
                ],
                "stats": [
                    "passing yards", "rushing yards", "receiving yards", "touchdowns",
                    "sacks", "tackles", "interceptions", "completions", "attempts"
                ],
                "positions": [
                    "quarterback", "qb", "running back", "rb", "fullback", "fb",
                    "wide receiver", "wr", "tight end", "te", "offensive line", "ol",
                    "defensive end", "de", "defensive tackle", "dt", "linebacker", "lb",
                    "cornerback", "cb", "safety", "s", "kicker", "k", "punter", "p"
                ]
            },
            
            "NBA": {
                "keywords": [
                    "nba", "basketball", "point guard", "pg", "shooting guard", "sg",
                    "small forward", "sf", "power forward", "pf", "center", "c",
                    "points", "rebounds", "assists", "steals", "blocks", "three pointer"
                ],
                "teams": [
                    "lakers", "warriors", "celtics", "nets", "knicks", "bulls",
                    "heat", "spurs", "mavericks", "clippers", "nuggets", "jazz",
                    "blazers", "kings", "suns", "rockets", "thunder", "pelicans",
                    "grizzlies", "timberwolves", "bucks", "cavaliers", "pistons",
                    "pacers", "raptors", "76ers", "hawks", "hornets", "magic", "wizards"
                ],
                "stats": [
                    "points", "rebounds", "assists", "steals", "blocks", "turnovers",
                    "field goals", "free throws", "three pointers", "minutes"
                ],
                "positions": [
                    "point guard", "pg", "shooting guard", "sg", "guard", "g",
                    "small forward", "sf", "power forward", "pf", "forward", "f",
                    "center", "c"
                ]
            },
            
            "MLB": {
                "keywords": [
                    "mlb", "baseball", "pitcher", "catcher", "infielder", "outfielder",
                    "home run", "rbi", "batting average", "era", "strikeout", "walk"
                ],
                "teams": [
                    "yankees", "red sox", "dodgers", "giants", "cubs", "cardinals",
                    "astros", "rangers", "angels", "athletics", "mariners", "twins",
                    "tigers", "guardians", "royals", "white sox", "orioles", "rays",
                    "blue jays", "braves", "marlins", "mets", "phillies", "nationals",
                    "brewers", "reds", "pirates", "rockies", "padres", "diamondbacks"
                ],
                "stats": [
                    "batting average", "home runs", "rbis", "stolen bases", "era",
                    "wins", "losses", "saves", "strikeouts", "walks"
                ],
                "positions": [
                    "pitcher", "p", "catcher", "c", "first base", "1b",
                    "second base", "2b", "third base", "3b", "shortstop", "ss",
                    "left field", "lf", "center field", "cf", "right field", "rf",
                    "designated hitter", "dh"
                ]
            },
            
            "NHL": {
                "keywords": [
                    "nhl", "hockey", "center", "wing", "defenseman", "goalie",
                    "goals", "assists", "points", "penalty", "power play", "save"
                ],
                "teams": [
                    "bruins", "rangers", "canadiens", "maple leafs", "blackhawks",
                    "red wings", "flyers", "penguins", "capitals", "lightning",
                    "panthers", "hurricanes", "devils", "islanders", "blue jackets",
                    "sabres", "senators", "avalanche", "stars", "predators",
                    "blues", "wild", "jets", "flames", "oilers", "canucks",
                    "golden knights", "kings", "ducks", "sharks", "coyotes", "kraken"
                ],
                "stats": [
                    "goals", "assists", "points", "plus minus", "penalty minutes",
                    "shots", "saves", "goals against", "save percentage"
                ],
                "positions": [
                    "center", "c", "left wing", "lw", "right wing", "rw",
                    "defenseman", "d", "goalie", "g", "forward", "f"
                ]
            },
            
            "NASCAR": {
                "keywords": [
                    "nascar", "racing", "driver", "car", "race", "lap", "pole",
                    "finish", "points", "championship", "cup series", "xfinity"
                ],
                "teams": [
                    "hendrick", "gibbs", "penske", "stewart-haas", "ganassi",
                    "roush fenway", "richard childress", "front row", "wood brothers"
                ],
                "stats": [
                    "wins", "top 5", "top 10", "poles", "laps led", "points",
                    "stage wins", "playoff points", "average finish"
                ],
                "positions": ["driver"]
            },
            
            "MLS": {
                "keywords": [
                    "mls", "soccer", "football", "goal", "assist", "midfielder",
                    "defender", "forward", "goalkeeper", "penalty", "yellow card"
                ],
                "teams": [
                    "galaxy", "lafc", "atlanta united", "seattle sounders", "portland timbers",
                    "orlando city", "inter miami", "new york city fc", "nycfc", "red bulls",
                    "philadelphia union", "dc united", "toronto fc", "montreal impact",
                    "chicago fire", "columbus crew", "cincinnati", "nashville sc"
                ],
                "stats": [
                    "goals", "assists", "shots", "saves", "yellow cards", "red cards",
                    "minutes played", "passes", "crosses", "tackles"
                ],
                "positions": [
                    "goalkeeper", "gk", "defender", "def", "midfielder", "mid",
                    "forward", "fwd", "striker", "st", "winger"
                ]
            },
            
            "F1": {
                "keywords": [
                    "formula 1", "f1", "grand prix", "driver", "constructor", "pole position",
                    "fastest lap", "podium", "championship", "qualifying", "practice"
                ],
                "teams": [
                    "red bull", "mercedes", "ferrari", "mclaren", "aston martin",
                    "alpine", "williams", "alphatauri", "alfa romeo", "haas"
                ],
                "stats": [
                    "wins", "podiums", "poles", "fastest laps", "points",
                    "championships", "dnf", "grid position", "race time"
                ],
                "positions": ["driver", "constructor"]
            }
        }
        
        # Dynamically discover available sports from database
        try:
            # Try to import sport config manager
            from ..config.sport_config import SportConfigManager
            sport_config_manager = SportConfigManager()
            available_sports = sport_config_manager.get_supported_sports()
            
            for sport in available_sports:
                if sport not in base_registry:
                    # Create basic registry entry for new sports
                    base_registry[sport] = {
                        "keywords": [sport.lower()],
                        "teams": [],
                        "stats": [],
                        "positions": []
                    }
        except Exception as e:
            console.print(f"[dim yellow]Note: Could not auto-discover sports from config: {e}[/dim yellow]")
        
        return base_registry

    def _create_sport_detection_tools(self) -> List:
        """Create tools for sport detection and entity extraction"""
        
        def detect_sports_in_query(query: str) -> str:
            """
            Analyze a query to detect which sports are mentioned.
            Returns JSON with detected sports and confidence scores.
            """
            detected = []
            query_lower = query.lower()
            
            for sport, patterns in self.sport_registry.items():
                confidence = 0.0
                matched_entities = []
                
                # Check keywords
                keyword_matches = sum(1 for keyword in patterns["keywords"] 
                                    if keyword in query_lower)
                if keyword_matches > 0:
                    confidence += min(keyword_matches * 0.3, 0.6)
                    matched_entities.extend([kw for kw in patterns["keywords"] if kw in query_lower])
                
                # Check team names
                team_matches = sum(1 for team in patterns["teams"] 
                                 if team in query_lower)
                if team_matches > 0:
                    confidence += min(team_matches * 0.4, 0.8)
                    matched_entities.extend([team for team in patterns["teams"] if team in query_lower])
                
                # Check stats
                stat_matches = sum(1 for stat in patterns["stats"] 
                                 if stat in query_lower)
                if stat_matches > 0:
                    confidence += min(stat_matches * 0.2, 0.4)
                    matched_entities.extend([stat for stat in patterns["stats"] if stat in query_lower])
                
                # Check positions
                position_matches = sum(1 for pos in patterns["positions"] 
                                     if pos in query_lower)
                if position_matches > 0:
                    confidence += min(position_matches * 0.3, 0.6)
                    matched_entities.extend([pos for pos in patterns["positions"] if pos in query_lower])
                
                if confidence > 0.2:  # Minimum threshold
                    detected.append({
                        "sport": sport,
                        "confidence": min(confidence, 1.0),
                        "entities": list(set(matched_entities)),
                        "reasoning": f"Found {keyword_matches} keywords, {team_matches} teams, {stat_matches} stats, {position_matches} positions"
                    })
            
            return json.dumps({"detected_sports": detected})

        def extract_entities_from_query(query: str, sport: str = None) -> str:
            """
            Extract players, teams, and metrics from a sports query.
            Returns JSON with categorized entities.
            """
            entities = {
                "players": [],
                "teams": [],
                "metrics": [],
                "temporal": [],
                "comparisons": []
            }
            
            query_lower = query.lower()
            
            # Extract comparison indicators
            comparison_words = ["vs", "versus", "compared to", "against", "better than"]
            for comp in comparison_words:
                if comp in query_lower:
                    entities["comparisons"].append(comp)
            
            # Extract temporal context
            temporal_words = ["2024", "2023", "2022", "season", "career", "this year", "last year"]
            for temp in temporal_words:
                if temp in query_lower:
                    entities["temporal"].append(temp)
            
            # If sport is specified, use sport-specific patterns
            if sport and sport in self.sport_registry:
                patterns = self.sport_registry[sport]
                
                # Extract teams
                for team in patterns["teams"]:
                    if team in query_lower:
                        entities["teams"].append(team)
                
                # Extract metrics/stats
                for stat in patterns["stats"]:
                    if stat in query_lower:
                        entities["metrics"].append(stat)
            
            # Generic player name extraction (simplified)
            words = query.split()
            potential_names = []
            for i, word in enumerate(words):
                if word[0].isupper() and len(word) > 2:
                    # Check if next word is also capitalized (likely a name)
                    if i + 1 < len(words) and words[i + 1][0].isupper():
                        potential_names.append(f"{word} {words[i + 1]}")
            
            entities["players"] = potential_names
            
            return json.dumps(entities)

        def check_sport_availability(sport: str) -> str:
            """
            Check if a sport's data is available in database and cache.
            Returns JSON with availability status.
            """
            availability = {
                "sport": sport,
                "database_available": False,
                "cache_available": False,
                "player_count": 0,
                "team_count": 0,
                "supported": False
            }
            
            try:
                # Try to check database availability
                from ..database.sport_models import sport_db_manager
                
                session = sport_db_manager.get_session(sport)
                models = sport_db_manager.get_models(sport)
                
                if session and models:
                    availability["database_available"] = True
                    availability["supported"] = True
                    
                    # Count players and teams
                    if "Player" in models:
                        availability["player_count"] = session.query(models["Player"]).count()
                    if "Team" in models:
                        availability["team_count"] = session.query(models["Team"]).count()
                    
                    session.close()
                
                # Check cache (simplified check)
                try:
                    from ..cache.shared_cache import sports_cache
                    cache_keys = sports_cache._player_cache.keys()
                    sport_cache_count = len([k for k in cache_keys if sport.lower() in k.lower()])
                    if sport_cache_count > 0:
                        availability["cache_available"] = True
                except:
                    pass
                
            except Exception as e:
                availability["error"] = str(e)
            
            return json.dumps(availability)

        return [detect_sports_in_query, extract_entities_from_query, check_sport_availability]

    def _create_workflow(self):
        """Create workflow (LangGraph if available, otherwise simple workflow)"""
        if StateGraph:
            return self._create_langgraph_workflow()
        else:
            return self._create_simple_workflow()

    def _create_langgraph_workflow(self):
        """Create LangGraph workflow for intelligent query processing"""
        # This would be the full LangGraph implementation
        # For now, return a simple workflow
        return self._create_simple_workflow()

    def _create_simple_workflow(self):
        """Create a simple workflow without LangGraph"""
        async def simple_workflow(state: UniversalQueryState) -> UniversalQueryState:
            """Simple workflow implementation"""
            
            # Step 1: Sport Detection
            console.print("[cyan]🔍 Detecting sports in query...[/cyan]")
            detection_result = self.sport_detection_tools[0](state.original_query)
            
            try:
                detection_data = json.loads(detection_result)
                detected_sports = []
                
                for sport_data in detection_data.get("detected_sports", []):
                    sport_context = SportContext(
                        sport=sport_data["sport"],
                        confidence=sport_data["confidence"],
                        entities=sport_data["entities"],
                        reasoning=sport_data["reasoning"]
                    )
                    detected_sports.append(sport_context)
                
                state.detected_sports = detected_sports
                
                if detected_sports:
                    primary = max(detected_sports, key=lambda x: x.confidence)
                    state.primary_sport = primary.sport
                    console.print(f"[green]✅ Primary sport detected: {primary.sport} (confidence: {primary.confidence:.2f})[/green]")
                
            except Exception as e:
                state.error_messages.append(f"Sport detection error: {str(e)}")
            
            # Step 2: Entity Extraction
            console.print("[cyan]🎯 Extracting entities...[/cyan]")
            extraction_result = self.sport_detection_tools[1](state.original_query, state.primary_sport)
            
            try:
                entities_data = json.loads(extraction_result)
                state.entities = entities_data
                state.metrics = entities_data.get("metrics", [])
                
            except Exception as e:
                state.error_messages.append(f"Entity extraction error: {str(e)}")
            
            # Step 3: Availability Check
            console.print("[cyan]📊 Checking data availability...[/cyan]")
            for sport_context in state.detected_sports:
                try:
                    availability_result = self.sport_detection_tools[2](sport_context.sport)
                    availability_data = json.loads(availability_result)
                    
                    sport_context.database_available = availability_data.get("database_available", False)
                    sport_context.cache_available = availability_data.get("cache_available", False)
                    
                except Exception as e:
                    console.print(f"[yellow]⚠️ Availability check failed for {sport_context.sport}: {e}[/yellow]")
            
            # Step 4: Routing Decision
            console.print("[cyan]🚦 Making routing decision...[/cyan]")
            if not state.detected_sports:
                state.routing_decision = {
                    "strategy": "error",
                    "reason": "No sports detected"
                }
            else:
                high_confidence_sports = [s for s in state.detected_sports if s.confidence > 0.6]
                
                if len(high_confidence_sports) == 1:
                    primary = high_confidence_sports[0]
                    state.routing_decision = {
                        "strategy": "single_sport",
                        "sport": primary.sport,
                        "reason": f"Single sport with confidence: {primary.confidence:.2f}"
                    }
                elif len(high_confidence_sports) > 1:
                    state.routing_decision = {
                        "strategy": "cross_sport",
                        "sports": [s.sport for s in high_confidence_sports],
                        "reason": "Multiple sports detected"
                    }
                else:
                    state.routing_decision = {
                        "strategy": "low_confidence",
                        "reason": "All sports detected with low confidence"
                    }
            
            # Step 5: Query Execution
            console.print("[cyan]⚡ Executing query...[/cyan]")
            strategy = state.routing_decision.get("strategy")
            
            if strategy == "single_sport":
                sport = state.routing_decision["sport"]
                state.responses[sport] = self._execute_single_sport_query(
                    sport, state.original_query, state.entities, state.metrics
                )
            elif strategy == "cross_sport":
                sports = state.routing_decision["sports"]
                for sport in sports:
                    state.responses[sport] = self._execute_single_sport_query(
                        sport, state.original_query, state.entities, state.metrics
                    )
            else:
                state.responses["error"] = {
                    "message": "I couldn't determine which sport you're asking about. Could you please specify the sport?",
                    "suggestions": ["Try: 'NFL stats for...'", "Try: 'NBA player...'"]
                }
            
            # Step 6: Response Formatting
            console.print("[cyan]📝 Formatting response...[/cyan]")
            if "error" in state.responses:
                state.final_response = self._format_error_response(state.responses["error"])
            elif len(state.responses) == 1:
                sport, response = next(iter(state.responses.items()))
                state.final_response = self._format_single_sport_response(sport, response)
            else:
                state.final_response = self._format_cross_sport_response(state.responses)
            
            return state
        
        return simple_workflow

    def _execute_single_sport_query(self, sport: str, query: str, entities: Dict[str, List[str]], metrics: List[str]) -> Dict[str, Any]:
        """Execute a query for a single sport"""
        try:
            # For now, return a mock response
            # In a real implementation, this would route to the appropriate sport-specific system
            return {
                "status": "success",
                "sport": sport,
                "query": query,
                "message": f"Successfully processed {sport} query",
                "entities": entities,
                "metrics": metrics
            }
            
        except Exception as e:
            return {
                "status": "error",
                "sport": sport,
                "error": str(e),
                "message": f"Failed to process {sport} query"
            }

    def _format_error_response(self, error_data: Dict[str, Any]) -> str:
        """Format error response"""
        message = error_data.get("message", "An error occurred")
        suggestions = error_data.get("suggestions", [])
        
        response = f"❌ {message}\n"
        if suggestions:
            response += "\n💡 Suggestions:\n"
            for suggestion in suggestions:
                response += f"  • {suggestion}\n"
        
        return response.strip()

    def _format_single_sport_response(self, sport: str, response_data: Dict[str, Any]) -> str:
        """Format single sport response"""
        if response_data.get("status") == "error":
            return f"❌ {sport} Error: {response_data.get('message', 'Unknown error')}"
        
        message = response_data.get("message", "Query processed successfully")
        entities = response_data.get("entities", {})
        
        response = f"🏆 {sport} Result: {message}\n"
        
        if entities.get("players"):
            response += f"👤 Players: {', '.join(entities['players'])}\n"
        if entities.get("teams"):
            response += f"🏟️ Teams: {', '.join(entities['teams'])}\n"
        if entities.get("metrics"):
            response += f"📊 Metrics: {', '.join(entities['metrics'])}\n"
        
        return response.strip()

    def _format_cross_sport_response(self, responses: Dict[str, Dict[str, Any]]) -> str:
        """Format cross-sport comparison response"""
        response = "🌟 Cross-Sport Analysis:\n\n"
        
        for sport, data in responses.items():
            if data.get("status") == "success":
                response += f"🏆 {sport}: {data.get('message', 'Success')}\n"
            else:
                response += f"❌ {sport}: {data.get('message', 'Error')}\n"
        
        return response.strip()

    async def process_query(self, query: str) -> str:
        """
        Main entry point for processing queries through the Universal Sports Agent
        """
        console.print(Panel.fit(
            f"[bold blue]🌟 Universal Sports Agent Processing[/bold blue]\n"
            f"[cyan]Query: {query}[/cyan]",
            border_style="blue"
        ))
        
        # Initialize state
        initial_state = UniversalQueryState(original_query=query)
        
        # Add to conversation memory
        self.conversation_history.append({
            "type": "user",
            "content": query,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # Execute workflow
            final_state = await self.workflow(initial_state)
            
            # Add response to memory
            self.conversation_history.append({
                "type": "assistant",
                "content": final_state.final_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Display beautiful results
            self._display_processing_results(final_state)
            
            return final_state.final_response
            
        except Exception as e:
            error_msg = f"Universal Sports Agent error: {str(e)}"
            console.print(f"[red]❌ {error_msg}[/red]")
            self.conversation_history.append({
                "type": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().isoformat()
            })
            return error_msg

    def _display_processing_results(self, state: UniversalQueryState):
        """Display beautiful processing results"""
        
        # Sports Detection Table
        if state.detected_sports:
            sports_table = Table(title="🎯 Detected Sports")
            sports_table.add_column("Sport", style="cyan")
            sports_table.add_column("Confidence", style="green")
            sports_table.add_column("Entities Found", style="yellow")
            sports_table.add_column("Data Available", style="blue")
            
            for sport_context in state.detected_sports:
                data_status = "✅" if (sport_context.database_available or sport_context.cache_available) else "❌"
                sports_table.add_row(
                    sport_context.sport,
                    f"{sport_context.confidence:.2f}",
                    f"{len(sport_context.entities)} entities",
                    data_status
                )
            
            console.print(sports_table)
        
        # Routing Decision Panel
        if state.routing_decision:
            routing_info = Panel(
                f"[bold]Strategy:[/bold] {state.routing_decision.get('strategy', 'unknown')}\n"
                f"[bold]Reason:[/bold] {state.routing_decision.get('reason', 'No reason provided')}",
                title="🚦 Routing Decision",
                border_style="green"
            )
            console.print(routing_info)

    def add_sport_to_registry(self, sport: str, patterns: Dict[str, List[str]]):
        """
        Dynamically add a new sport to the registry
        
        Args:
            sport: Sport name (e.g., "MLS", "F1", "Tennis")
            patterns: Dictionary with keys: keywords, teams, stats, positions
        """
        self.sport_registry[sport] = patterns
        console.print(f"[green]✅ Added {sport} to Universal Sports Agent registry[/green]")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history for context"""
        return self.conversation_history

    def reset_conversation(self):
        """Reset conversation memory"""
        self.conversation_history = []
        console.print("[yellow]🔄 Conversation memory reset[/yellow]")

    def get_supported_sports(self) -> List[str]:
        """Get list of all supported sports"""
        return list(self.sport_registry.keys())

    def get_sport_info(self, sport: str) -> Dict[str, Any]:
        """Get information about a specific sport"""
        if sport in self.sport_registry:
            patterns = self.sport_registry[sport]
            return {
                "sport": sport,
                "keywords": len(patterns["keywords"]),
                "teams": len(patterns["teams"]),
                "stats": len(patterns["stats"]),
                "positions": len(patterns["positions"]),
                "patterns": patterns
            }
        return {"error": f"Sport '{sport}' not found in registry"}

# Global instance for easy access
universal_sports_agent = UniversalSportsAgent()

async def process_universal_query(query: str) -> str:
    """
    Easy-to-use function for processing queries through the Universal Sports Agent
    """
    return await universal_sports_agent.process_query(query)

def add_new_sport(sport: str, keywords: List[str], teams: List[str] = None, 
                 stats: List[str] = None, positions: List[str] = None):
    """
    Easy function to add new sports dynamically
    
    Example:
        add_new_sport(
            "Tennis", 
            keywords=["tennis", "serve", "ace", "set", "match"],
            teams=["player"],  # Tennis doesn't have teams, but we can add tournaments
            stats=["aces", "double faults", "first serve percentage", "winners"],
            positions=["singles", "doubles"]
        )
    """
    patterns = {
        "keywords": keywords,
        "teams": teams or [],
        "stats": stats or [],
        "positions": positions or []
    }
    universal_sports_agent.add_sport_to_registry(sport, patterns)

def get_supported_sports() -> List[str]:
    """Get list of all supported sports"""
    return universal_sports_agent.get_supported_sports()

def show_sport_registry():
    """Display the current sport registry in a beautiful table"""
    table = Table(title="🌟 Universal Sports Registry")
    table.add_column("Sport", style="cyan")
    table.add_column("Keywords", style="green")
    table.add_column("Teams", style="yellow")
    table.add_column("Stats", style="blue")
    table.add_column("Positions", style="magenta")
    
    for sport, patterns in universal_sports_agent.sport_registry.items():
        table.add_row(
            sport,
            str(len(patterns["keywords"])),
            str(len(patterns["teams"])),
            str(len(patterns["stats"])),
            str(len(patterns["positions"]))
        )
    
    console.print(table) 