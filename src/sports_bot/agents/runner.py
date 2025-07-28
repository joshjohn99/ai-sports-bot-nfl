"""
Agent Runner Implementation using OpenAI Agents SDK.

This module provides a runner for executing sports debate agents using
the OpenAI Agents SDK. It handles agent orchestration, streaming output,
and error handling.

Example:
    ```python
    # Initialize runner
    runner = AgentRunner()
    
    # Process query synchronously
    result = await runner.process_query(
        "Compare Kyler Murray and Josh Allen",
        context={"focus": "passing stats"}
    )
    
    # Process query with streaming
    async for partial in runner.process_query_stream(
        "Who's the better QB?",
        context={"timeframe": "2023 season"}
    ):
        print(partial["content"])
    ```

Note:
    This implementation follows OpenAI's best practices for:
    - Deterministic agent execution
    - Streaming response handling
    - Error recovery and logging
    - Context management
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator, TypedDict, Union
from agents import Agent, Runner as SDKRunner

from sports_bot.agents.agent_config import AgentConfig, AgentRole
from sports_bot.core.exceptions import AgentError
from sports_bot.core.logging_config import setup_logging

# Configure logging
logger = setup_logging(log_level="DEBUG", app_name="sports_bot.agents.runner")

class AgentOutput(TypedDict):
    """Type definition for agent output."""
    type: str  # "final" or "progress"
    content: Union[str, Dict[str, Any]]

class AgentContext(TypedDict, total=False):
    """Type definition for agent context."""
    focus: str  # Analysis focus (e.g., "passing stats")
    timeframe: str  # Time period to consider
    metrics: List[str]  # Specific metrics to analyze
    team_context: Dict[str, Any]  # Team-specific context

class AgentRunner:
    """
    Agent runner using OpenAI Agents SDK.
    
    This class manages the execution of sports debate agents,
    handling both synchronous and streaming interactions. It
    provides context management, error handling, and consistent
    output formatting.
    
    Features:
        - Agent orchestration: Manages agent lifecycle
        - Handoff management: Handles agent transitions
        - Error handling: Consistent error recovery
        - Tracing support: Execution monitoring
        - Context management: Structured context passing
        - Streaming: Real-time result generation
    
    Attributes:
        debate_agent: Primary debate agent instance
    """
    
    def __init__(self):
        """
        Initialize agent runner.
        
        This constructor sets up the debate agent with appropriate
        configuration and initializes logging.
        """
        # Initialize debate agent
        debate_config = AgentConfig.get_debate_config()
        self.debate_agent = Agent(
            name="debate_agent",
            instructions=debate_config.instructions,
            mcp_config={
                "temperature": debate_config.guardrails.temperature,
                "max_tokens": debate_config.guardrails.max_tokens
            }
        )
        
        logger.info("Initialized AgentRunner")
    
    async def process_query(
        self,
        query: str,
        context: Optional[AgentContext] = None
    ) -> AgentOutput:
        """
        Process query through debate agent.
        
        This method executes a query synchronously, waiting for
        the complete response before returning.
        
        Args:
            query: User's question or comparison request
            context: Optional execution context with additional
                    parameters like focus areas or time frames
            
        Returns:
            Dictionary containing:
            - type: Output type ("final" or "progress")
            - content: Response content (string or structured data)
            
        Raises:
            AgentError: If query processing fails
            
        Example:
            ```python
            result = await runner.process_query(
                "Compare Murray and Allen",
                context={"focus": "passing efficiency"}
            )
            print(result["content"])
            ```
        """
        try:
            # Add context to query if provided
            input_text = self._format_input(query, context)
            
            # Run through debate agent
            result = await SDKRunner.run(
                self.debate_agent,
                input=input_text
            )
            
            return self._format_output(result)
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise AgentError(f"Failed to process query: {str(e)}")
    
    async def process_query_stream(
        self,
        query: str,
        context: Optional[AgentContext] = None
    ) -> AsyncGenerator[AgentOutput, None]:
        """
        Process query with streaming output.
        
        This method executes a query and streams the results as they
        become available, allowing for real-time updates.
        
        Args:
            query: User's question or comparison request
            context: Optional execution context with additional
                    parameters like focus areas or time frames
            
        Yields:
            Dictionary containing:
            - type: Output type ("final" or "progress")
            - content: Response content (string or structured data)
            
        Raises:
            AgentError: If streaming fails
            
        Example:
            ```python
            async for result in runner.process_query_stream(
                "Compare Murray and Allen",
                context={"timeframe": "last 5 games"}
            ):
                print(f"Progress: {result['content']}")
            ```
        """
        try:
            # Add context to query if provided
            input_text = self._format_input(query, context)
            
            # Stream results from debate agent
            async for result in SDKRunner.run_stream(
                self.debate_agent,
                input=input_text
            ):
                yield self._format_output(result)
            
        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            raise AgentError(f"Failed to stream query: {str(e)}")
    
    def _format_input(
        self,
        query: str,
        context: Optional[AgentContext] = None
    ) -> str:
        """
        Format input for agent consumption.
        
        This method combines the user query with optional context
        into a structured format that the agent can process.
        
        Args:
            query: User's question or comparison request
            context: Optional execution context
            
        Returns:
            Formatted input string with query and context
            
        Example:
            ```python
            input_text = runner._format_input(
                "Compare QBs",
                {"focus": "accuracy", "timeframe": "2023"}
            )
            # Results in:
            # Compare QBs
            #
            # Context:
            # focus: accuracy
            # timeframe: 2023
            ```
        """
        if not context:
            return query
        
        # Add context to query
        context_parts = []
        for key, value in context.items():
            if isinstance(value, dict):
                context_parts.append(f"{key}:")
                for k, v in value.items():
                    context_parts.append(f"  {k}: {v}")
            else:
                context_parts.append(f"{key}: {value}")
        
        return f"{query}\n\nContext:\n" + "\n".join(context_parts)
    
    def _format_output(self, result: Any) -> AgentOutput:
        """
        Format agent output.
        
        This method standardizes the agent's output format, handling
        both final results and streaming progress updates.
        
        Args:
            result: Raw agent result (may be structured or string)
            
        Returns:
            Dictionary containing:
            - type: "final" for complete results, "progress" for updates
            - content: Formatted response content
            
        Example:
            ```python
            # Final output
            output = runner._format_output(final_result)
            # {"type": "final", "content": {"conclusion": "..."}}
            
            # Progress update
            output = runner._format_output(partial_result)
            # {"type": "progress", "content": "Analyzing stats..."}
            ```
        """
        if hasattr(result, "final_output"):
            # Handle structured output
            return {
                "type": "final",
                "content": result.final_output
            }
        else:
            # Handle streaming/intermediate output
            return {
                "type": "progress",
                "content": str(result)
            } 