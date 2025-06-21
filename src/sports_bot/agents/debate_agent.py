"""
Debate Agent for handling complex sports queries using LangChain
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, Any, List

class LLMDebateAgent:
    """A debate agent using LangChain for handling complex sports queries."""
    
    def __init__(self, model="gpt-4"):
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.7,
            streaming=False
        )
        self.context = {}
        self._setup_debate_chain()

    def _setup_debate_chain(self):
        """Setup LangChain chain for debate generation"""
        debate_template = """You are a sports debate analyst. Compare {player_a} and {player_b} in the context of '{debate_type}'.

Here is the evidence:
{evidence}

Generate a debate-style argument explaining who is better and why. Provide a balanced view, highlight the strengths of each, and deliver an engaging, fan-style take.

Analysis:"""
        
        self.debate_prompt = PromptTemplate(
            input_variables=["player_a", "player_b", "debate_type", "evidence"],
            template=debate_template
        )
        
        # Use the new LangChain pattern: prompt | llm
        self.debate_chain = self.debate_prompt | self.llm

    def generate_dynamic_debate(self, playerA: Dict[str, Any], playerB: Dict[str, Any], 
                               evidence_list: List[Dict], debate_type: str) -> str:
        """Generate debate using LangChain chain"""
        
        # Build evidence string
        evidence_parts = []
        for e in evidence_list:
            stat = e['stat']
            valueA = playerA['stats'].get(stat, 'unknown')
            valueB = playerB['stats'].get(stat, 'unknown')
            evidence_parts.append(f"- {stat}: {playerA['name']} has {valueA}, {playerB['name']} has {valueB}")
        
        evidence_text = "\n".join(evidence_parts)
        
        # Use LangChain chain to generate debate
        try:
            result = self.debate_chain.invoke({
                "player_a": playerA['name'],
                "player_b": playerB['name'],
                "debate_type": debate_type,
                "evidence": evidence_text
            })
            return result.content.strip()
        except Exception as e:
            return f"Error generating debate: {str(e)}"

    async def debate_async(self, query: str) -> str:
        """
        Async version for debate processing using LangChain
        """
        try:
            messages = [
                SystemMessage(content="You are a sports debate expert who provides balanced, engaging analysis."),
                HumanMessage(content=f"Analyze this sports query: {query}")
            ]
            result = await self.llm.ainvoke(messages)
            return result.content
        except Exception as e:
            return f"Error in async debate: {str(e)}"

    def debate(self, query: str) -> str:
        """
        Process a complex query through debate-style reasoning using LangChain.
        """
        try:
            messages = [
                SystemMessage(content="You are a sports debate expert who provides balanced, engaging analysis."),
                HumanMessage(content=f"Analyze this sports query: {query}")
            ]
            result = self.llm.invoke(messages)
            return result.content
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def validate_response(self, response: str) -> bool:
        """
        Validate a response through debate-style reasoning.
        Enhanced validation using LangChain.
        """
        if not response or len(response.strip()) < 10:
            return False
        
        # Could add more sophisticated validation using LangChain tools
        # For now, basic validation
        return True

    def create_comparison_chain(self, metrics: List[str]):
        """Create a specialized chain for player comparisons"""
        comparison_template = """Compare these players across the following metrics: {metrics}

Player Data:
{player_data}

Provide a detailed analysis focusing on:
1. Statistical comparison
2. Strengths and weaknesses of each player
3. Context and situational factors
4. Overall assessment

Analysis:"""
        
        comparison_prompt = PromptTemplate(
            input_variables=["metrics", "player_data"],
            template=comparison_template
        )
        
        # Return the new chain pattern
        return comparison_prompt | self.llm