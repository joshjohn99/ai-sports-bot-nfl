"""
Agent configuration and types.

This module provides configuration structures and type definitions for
the sports debate agent system. It defines agent roles, guardrails,
and output formats for structured debates.

Example:
    ```python
    # Create debate agent config
    config = AgentConfig.get_debate_config()
    
    # Create custom config
    config = AgentConfig(
        role=AgentRole.DEBATE,
        instructions="Custom instructions",
        guardrails=AgentGuardrails(max_turns=3)
    )
    
    # Create debate output
    output = DebateOutputType(
        topic="Who's the better QB?",
        arguments=[
            DebateArgument("Kyler Murray", "Strong arm", {"completions": 245}),
            DebateArgument("Josh Allen", "Dual threat", {"rushingYards": 476})
        ],
        conclusion="Josh Allen has edge in versatility",
        confidence=0.85
    )
    ```
"""

from enum import Enum
from typing import List, Dict, Any, Optional, TypedDict
from dataclasses import dataclass, field

class AgentRole(Enum):
    """
    Agent roles in the sports debate system.
    
    This enum defines the different specialized roles that agents
    can take in processing sports-related queries.
    
    Roles:
        TRIAGE: Initial query analysis and routing
        DEBATE: Player and team comparisons
        STATS: Statistical analysis and insights
        COMMENTARY: General sports discussion and context
    """
    TRIAGE = "triage"
    DEBATE = "debate"
    STATS = "stats"
    COMMENTARY = "commentary"

class StatDict(TypedDict, total=False):
    """Type definition for player statistics."""
    completions: int
    passingYards: int
    touchdowns: int
    interceptions: int
    rushingYards: int
    receptions: int
    receivingYards: int

@dataclass
class AgentGuardrails:
    """
    Agent guardrails configuration.
    
    This class defines operational limits and parameters for
    controlling agent behavior and resource usage.
    
    Attributes:
        max_turns: Maximum conversation turns before termination
        max_tokens: Maximum tokens in a single response
        temperature: Response randomness (0.0-1.0)
        top_p: Nucleus sampling parameter (0.0-1.0)
        presence_penalty: Penalty for repeating topics (-2.0 to 2.0)
        frequency_penalty: Penalty for repeating words (-2.0 to 2.0)
        
    Note:
        Lower temperature and top_p values produce more focused,
        deterministic responses, while higher values increase creativity
        and variation.
    """
    max_turns: int = 5
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 0.9
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0

@dataclass
class DebateArgument:
    """
    Structure for debate arguments.
    
    This class represents a single argument in a sports debate,
    including the player being discussed, the argument text,
    and supporting statistics.
    
    Attributes:
        player: Name of the player being discussed
        argument: Main argument text
        stats: Optional dictionary of relevant statistics
        
    Example:
        ```python
        arg = DebateArgument(
            player="Kyler Murray",
            argument="Elite passing accuracy",
            stats={"completions": 245, "passingYards": 2800}
        )
        ```
    """
    player: str
    argument: str
    stats: Optional[StatDict] = None

@dataclass
class DebateOutputType:
    """
    Structured output for debates.
    
    This class defines the standard format for debate responses,
    ensuring consistent structure and including confidence metrics.
    
    Attributes:
        topic: Main debate topic or question
        arguments: List of arguments for each side
        conclusion: Final debate conclusion
        confidence: Confidence score (0.0-1.0) in conclusion
        
    Example:
        ```python
        output = DebateOutputType(
            topic="Who's the better quarterback?",
            arguments=[
                DebateArgument("Murray", "Accurate passer"),
                DebateArgument("Allen", "Dual threat")
            ],
            conclusion="Allen's versatility gives him the edge",
            confidence=0.85
        )
        ```
    """
    topic: str
    arguments: List[DebateArgument]
    conclusion: str
    confidence: float

@dataclass
class AgentConfig:
    """
    Agent configuration.
    
    This class provides complete configuration for an agent instance,
    including its role, instructions, operational guardrails, and
    available tools.
    
    Attributes:
        role: Agent's specialized role
        instructions: Detailed behavior instructions
        guardrails: Operational limits and parameters
        tools: Optional list of available tool names
        
    Example:
        ```python
        config = AgentConfig(
            role=AgentRole.DEBATE,
            instructions="Compare players objectively...",
            guardrails=AgentGuardrails(max_turns=3),
            tools=["stats_lookup", "player_compare"]
        )
        ```
    """
    role: AgentRole
    instructions: str
    guardrails: AgentGuardrails
    tools: Optional[List[str]] = None
    
    @classmethod
    def get_triage_config(cls) -> 'AgentConfig':
        """
        Get triage agent configuration.
        
        This method returns a pre-configured AgentConfig instance
        for the triage role, which handles initial query analysis
        and routing to specialized agents.
        
        Returns:
            AgentConfig with triage-specific settings
            
        Example:
            ```python
            triage = AgentConfig.get_triage_config()
            agent = TriageAgent(triage)
            ```
        """
        return cls(
            role=AgentRole.TRIAGE,
            instructions="""
            You are a triage agent for sports-related queries.
            Your role is to:
            1. Understand the user's query
            2. Determine the most appropriate specialized agent
            3. Route the query to that agent
            
            Available agents:
            - Debate: For comparing players/teams
            - Stats: For detailed statistics analysis
            - Commentary: For general sports discussion
            """,
            guardrails=AgentGuardrails(max_turns=3)
        )
    
    @classmethod
    def get_debate_config(cls) -> 'AgentConfig':
        """
        Get debate agent configuration.
        
        This method returns a pre-configured AgentConfig instance
        for the debate role, which handles player and team
        comparisons with statistical support.
        
        Returns:
            AgentConfig with debate-specific settings
            
        Example:
            ```python
            config = AgentConfig.get_debate_config()
            agent = DebateAgent(config)
            ```
        """
        return cls(
            role=AgentRole.DEBATE,
            instructions="""
            You are a sports debate agent.
            Your role is to:
            1. Compare players/teams objectively
            2. Use statistics to support arguments
            3. Consider context and recent performance
            4. Provide clear conclusions
            
            Format your response as:
            1. Topic
            2. Arguments for each player
            3. Statistical support
            4. Conclusion with confidence level
            """,
            guardrails=AgentGuardrails(),
            tools=["stats_lookup", "player_compare", "context_search"]
        ) 