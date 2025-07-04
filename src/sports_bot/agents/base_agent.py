"""
Base Agent Implementation

This module provides a base agent implementation following OpenAI Agents SDK patterns.
It implements core agent functionality including lifecycle management, streaming,
and tool integration.

Key Features:
1. Deterministic workflows - Predictable execution patterns
2. Dynamic system prompts - Runtime-configurable agent behavior
3. Streaming outputs - Real-time result generation
4. Lifecycle events - Execution monitoring and metrics
5. Agent as tools - Composable agent capabilities

Example:
    ```python
    class MyAgent(BaseAgent):
        async def _execute(self, query_context, agent_context):
            # Implement agent logic
            return {"result": "success"}
            
        async def _execute_stream(self, query_context, agent_context):
            # Implement streaming logic
            yield {"progress": 0.5}
            yield {"result": "success"}
            
    # Use the agent
    agent = MyAgent("my_agent_1")
    result = await agent.execute(query_context)
    ```
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator, Union, TypeVar, Generic
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from sports_bot.core.exceptions import AgentError
from sports_bot.core.logging_config import setup_logging

# Configure logging
logger = setup_logging(log_level="DEBUG", app_name="sports_bot.agents")

# Type variables for generic types
QueryContext = TypeVar('QueryContext')
AgentResult = TypeVar('AgentResult')

class AgentState(Enum):
    """
    Agent execution states.
    
    This enum defines the possible states an agent can be in during
    its execution lifecycle.
    
    States:
        INITIALIZED: Agent has been created but not started
        PROCESSING: Agent is executing synchronously
        STREAMING: Agent is generating streaming results
        COMPLETED: Agent has finished successfully
        FAILED: Agent encountered an error
    """
    INITIALIZED = "initialized"
    PROCESSING = "processing"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentContext:
    """
    Context for agent execution.
    
    This class maintains the state and metadata for a single
    agent execution instance.
    
    Attributes:
        agent_id: Unique identifier for the agent
        query_id: Unique identifier for the query being processed
        user_id: Identifier of the user making the request
        start_time: Timestamp when execution started
        state: Current execution state
        error: Error message if execution failed
        metrics: Execution metrics and statistics
    """
    agent_id: str
    query_id: str
    user_id: str
    start_time: float
    state: AgentState = AgentState.INITIALIZED
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

class AgentLifecycle:
    """
    Agent lifecycle management.
    
    This class handles the emission and processing of lifecycle
    events during agent execution. It supports registration of
    multiple event listeners for monitoring and metrics collection.
    
    Events:
        start: Agent execution started
        state_change: Agent state updated
        error: Error occurred during execution
        complete: Execution finished (success or failure)
    """
    
    def __init__(self):
        """Initialize lifecycle manager with empty listener list."""
        self.listeners: List[callable] = []
    
    def add_listener(self, listener: callable) -> None:
        """
        Add lifecycle event listener.
        
        Args:
            listener: Async callable that takes event name and data
                    Function signature: async def(event: str, data: Dict[str, Any])
        """
        self.listeners.append(listener)
    
    async def emit(self, event: str, data: Dict[str, Any]) -> None:
        """
        Emit lifecycle event to all listeners.
        
        Args:
            event: Name of the event
            data: Event data dictionary
            
        Note:
            Listener errors are caught and logged but don't stop event propagation
        """
        for listener in self.listeners:
            try:
                await listener(event, data)
            except Exception as e:
                logger.error(f"Error in lifecycle listener: {e}")

class BaseAgent(ABC, Generic[QueryContext, AgentResult]):
    """
    Base agent implementation with OpenAI SDK patterns.
    
    This abstract base class provides the core functionality for
    implementing agents. It handles lifecycle management, streaming,
    and tool integration while leaving the actual execution logic
    to concrete implementations.
    
    Features:
        - Deterministic workflow management
        - Dynamic system prompts
        - Streaming output support
        - Lifecycle events
        - Agent as tool capability
        
    Type Parameters:
        QueryContext: Type of the query context
        AgentResult: Type of the execution result
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize base agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
        """
        self.agent_id = agent_id
        self.lifecycle = AgentLifecycle()
        self.system_prompt: Optional[str] = None
        
        # Register default lifecycle listeners
        self.lifecycle.add_listener(self._log_lifecycle_event)
        
        logger.info(f"Initialized agent {agent_id}")
    
    async def _log_lifecycle_event(self, event: str, data: Dict[str, Any]) -> None:
        """
        Log lifecycle events.
        
        This is a default lifecycle listener that logs all events
        at INFO level.
        
        Args:
            event: Event name
            data: Event data
        """
        logger.info(f"Agent {self.agent_id} - {event}: {data}")
    
    def set_system_prompt(self, prompt: str) -> None:
        """
        Set dynamic system prompt.
        
        The system prompt controls the agent's behavior and can be
        updated at runtime.
        
        Args:
            prompt: New system prompt text
        """
        self.system_prompt = prompt
    
    async def execute(
        self,
        query_context: QueryContext,
        stream: bool = False
    ) -> Union[AgentResult, AsyncGenerator[AgentResult, None]]:
        """
        Execute agent with lifecycle management.
        
        This is the main entry point for agent execution. It handles:
        - Context creation
        - Lifecycle event emission
        - State management
        - Error handling
        - Streaming vs synchronous execution
        
        Args:
            query_context: Context object for this execution
            stream: Whether to stream results or return final result
            
        Returns:
            Either final result or async generator of streaming results
            
        Raises:
            AgentError: If execution fails
            
        Example:
            ```python
            # Synchronous execution
            result = await agent.execute(context)
            
            # Streaming execution
            async for partial in agent.execute(context, stream=True):
                print(partial)
            ```
        """
        # Create execution context
        context = AgentContext(
            agent_id=self.agent_id,
            query_id=query_context.query_id,
            user_id=query_context.user_id,
            start_time=asyncio.get_event_loop().time()
        )
        
        try:
            # Emit start event
            await self.lifecycle.emit("start", {
                "agent_id": self.agent_id,
                "query_id": context.query_id
            })
            
            # Update state
            context.state = AgentState.PROCESSING
            await self.lifecycle.emit("state_change", {
                "agent_id": self.agent_id,
                "state": context.state.value
            })
            
            if stream:
                # Stream results
                context.state = AgentState.STREAMING
                await self.lifecycle.emit("state_change", {
                    "agent_id": self.agent_id,
                    "state": context.state.value
                })
                
                async for result in self._execute_stream(query_context, context):
                    yield result
            else:
                # Execute synchronously
                result = await self._execute(query_context, context)
                
                # Update state
                context.state = AgentState.COMPLETED
                await self.lifecycle.emit("state_change", {
                    "agent_id": self.agent_id,
                    "state": context.state.value
                })
                
                return result
            
        except Exception as e:
            # Handle failure
            context.state = AgentState.FAILED
            context.error = str(e)
            
            await self.lifecycle.emit("error", {
                "agent_id": self.agent_id,
                "error": str(e)
            })
            
            raise AgentError(f"Agent execution failed: {str(e)}")
            
        finally:
            # Emit completion
            duration = asyncio.get_event_loop().time() - context.start_time
            await self.lifecycle.emit("complete", {
                "agent_id": self.agent_id,
                "duration": duration,
                "state": context.state.value,
                "error": context.error
            })
    
    @abstractmethod
    async def _execute(
        self,
        query_context: QueryContext,
        agent_context: AgentContext
    ) -> AgentResult:
        """
        Execute agent logic.
        
        This abstract method must be implemented by concrete agent classes
        to provide the core execution logic.
        
        Args:
            query_context: Context object for this execution
            agent_context: Agent execution context
            
        Returns:
            Execution result
            
        Note:
            This method should not handle lifecycle events or state management,
            as that is handled by the execute() method.
        """
        pass
    
    @abstractmethod
    async def _execute_stream(
        self,
        query_context: QueryContext,
        agent_context: AgentContext
    ) -> AsyncGenerator[AgentResult, None]:
        """
        Execute agent logic with streaming output.
        
        This abstract method must be implemented by concrete agent classes
        to provide streaming execution logic.
        
        Args:
            query_context: Context object for this execution
            agent_context: Agent execution context
            
        Yields:
            Partial execution results
            
        Note:
            This method should not handle lifecycle events or state management,
            as that is handled by the execute() method.
        """
        pass

    async def as_tool(
        self,
        tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute agent as a tool.
        
        This method allows the agent to be used as a tool by other agents.
        It provides a simplified interface that accepts a dictionary input
        and returns a dictionary output.
        
        Args:
            tool_input: Tool input parameters
            
        Returns:
            Tool execution result
            
        Example:
            ```python
            # Use agent as tool
            result = await agent.as_tool({
                "action": "analyze",
                "data": {"key": "value"}
            })
            ```
        """
        # Create minimal context
        context = AgentContext(
            agent_id=self.agent_id,
            query_id=f"tool_{self.agent_id}_{id(tool_input)}",
            user_id="system",
            start_time=asyncio.get_event_loop().time()
        )
        
        try:
            # Execute as tool
            return await self._execute_as_tool(tool_input, context)
        except Exception as e:
            raise AgentError(f"Tool execution failed: {str(e)}")

    @abstractmethod
    async def _execute_as_tool(
        self,
        tool_input: Dict[str, Any],
        agent_context: AgentContext
    ) -> Dict[str, Any]:
        """
        Execute agent logic when used as tool.
        
        This abstract method must be implemented by concrete agent classes
        to provide tool execution logic.
        
        Args:
            tool_input: Tool input parameters
            agent_context: Agent execution context
            
        Returns:
            Tool execution result
            
        Note:
            This method should focus on the core tool logic and not worry
            about error handling or context management.
        """
        pass 