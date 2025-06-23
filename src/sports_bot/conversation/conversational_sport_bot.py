"""
Complete Conversational Sports Bot - Enhanced with Memory and Context
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# LangChain imports
try:
    from langchain.memory import ConversationBufferMemory
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Your existing components
from ..agents.sports_agents import (
    run_query_planner, 
    run_enhanced_query_processor, 
    format_enhanced_response,
    QueryContext
)

# Rich for output
from rich.console import Console

console = Console()

@dataclass
class ConversationState:
    """Track conversation state across interactions"""
    user_id: str
    session_id: str
    last_player: Optional[str] = None
    last_team: Optional[str] = None
    last_stat_type: Optional[str] = None
    last_sport: Optional[str] = None
    query_count: int = 0
    favorite_players: List[str] = None
    
    def __post_init__(self):
        if self.favorite_players is None:
            self.favorite_players = []

class ConversationalSportsBot:
    """Enhanced conversational sports bot with memory and intelligence"""
    
    def __init__(self):
        self.conversation_states: Dict[str, ConversationState] = {}
        
        # Initialize LangChain components if available
        if LANGCHAIN_AVAILABLE:
            try:
                self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
                self.memory = ConversationBufferMemory(return_messages=True)
                console.print("[green]✅ LangChain components initialized![/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ LangChain setup issue: {e}[/yellow]")
                self.llm = None
                self.memory = None
        else:
            console.print("[yellow]⚠️ LangChain not available, using basic memory[/yellow]")
            self.llm = None
            self.memory = None
        
        console.print("[green]🤖 Conversational Sports Bot initialized![/green]")
    
    async def process_conversation(self, user_query: str, user_id: str = "default_user") -> str:
        """Process a conversational query with full context awareness"""
        
        try:
            # Get or create conversation state
            if user_id not in self.conversation_states:
                self.conversation_states[user_id] = ConversationState(
                    user_id=user_id,
                    session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            
            state = self.conversation_states[user_id]
            state.query_count += 1
            
            console.print(f"[dim]Query #{state.query_count} from {user_id}[/dim]")
            
            # Step 1: Enhance query with context
            enhanced_query = self._enhance_query_with_context(user_query, state)
            
            # Step 2: Check for clarification needs
            clarification = self._check_clarification_needed(enhanced_query, state)
            if clarification:
                self._log_interaction(user_query, clarification, state)
                return clarification
            
            # Step 3: Process the enhanced query
            console.print(f"[cyan]🔍 Processing: {enhanced_query}[/cyan]")
            
            # Use your existing enhanced system
            query_context = await run_query_planner(enhanced_query)
            sports_response = await run_enhanced_query_processor(enhanced_query, query_context)
            basic_response = format_enhanced_response(sports_response)
            
            # Step 4: Enhance response with conversational intelligence
            final_response = self._enhance_response(basic_response, sports_response, query_context, state)
            
            # Step 5: Update conversation state
            self._update_conversation_state(query_context, sports_response, state)
            
            # Step 6: Log the interaction
            self._log_interaction(user_query, final_response, state)
            
            return final_response
            
        except Exception as e:
            error_response = f"🤖 I encountered an issue processing your question: {str(e)}\n\n💡 Try rephrasing your question or asking about NFL stats!"
            console.print(f"[red]Error in conversation processing: {e}[/red]")
            return error_response
    
    def _enhance_query_with_context(self, user_query: str, state: ConversationState) -> str:
        """Enhance query with conversation context - THE MAGIC HAPPENS HERE! ✨"""
        
        enhanced_query = user_query
        query_lower = user_query.lower().strip()
        
        # 🔄 Handle pronoun references (he/his/him/that player)
        if any(pronoun in query_lower for pronoun in ["he ", "his ", "him ", " he", "that player"]):
            if state.last_player:
                # Replace pronouns with the actual player name
                enhanced_query = enhanced_query.replace(" he ", f" {state.last_player} ")
                enhanced_query = enhanced_query.replace("He ", f"{state.last_player} ")
                enhanced_query = enhanced_query.replace(" his ", f" {state.last_player}'s ")
                enhanced_query = enhanced_query.replace("His ", f"{state.last_player}'s ")
                enhanced_query = enhanced_query.replace(" him ", f" {state.last_player} ")
                enhanced_query = enhanced_query.replace("Him ", f"{state.last_player} ")
                enhanced_query = enhanced_query.replace("that player", state.last_player)
                
                console.print(f"[bold green]🔄 PRONOUN RESOLVED![/bold green]")
                console.print(f"[dim cyan]'{user_query}' → '{enhanced_query}'[/dim cyan]")
            else:
                console.print(f"[yellow]🔄 Pronoun detected but no previous player context[/yellow]")
        
        # 🎯 Handle "what about [stat]" patterns
        if query_lower.startswith("what about") and state.last_player:
            stat_part = enhanced_query.replace("what about", "").replace("What about", "").strip()
            enhanced_query = f"{state.last_player} {stat_part}"
            console.print(f"[bold green]🎯 CONTEXT ADDED![/bold green]")
            console.print(f"[dim cyan]'{user_query}' → '{enhanced_query}'[/dim cyan]")
        
        # 📊 Handle "more stats" / "other stats" requests
        if any(phrase in query_lower for phrase in ["more stats", "other stats", "additional stats", "show me more"]):
            if state.last_player:
                enhanced_query = f"{state.last_player} comprehensive stats"
                console.print(f"[bold green]📊 STATS EXPANDED![/bold green]")
                console.print(f"[dim cyan]'{user_query}' → '{enhanced_query}'[/dim cyan]")
        
        # 🆚 Handle comparison patterns like "compare him to [player]"
        if "compare" in query_lower and any(pronoun in query_lower for pronoun in ["him", "he"]):
            if state.last_player:
                enhanced_query = enhanced_query.replace(" him ", f" {state.last_player} ")
                enhanced_query = enhanced_query.replace(" he ", f" {state.last_player} ")
                console.print(f"[bold green]🆚 COMPARISON ENHANCED![/bold green]")
                console.print(f"[dim cyan]'{user_query}' → '{enhanced_query}'[/dim cyan]")
        
        return enhanced_query
    
    def _check_clarification_needed(self, enhanced_query: str, state: ConversationState) -> Optional[str]:
        """Check if we need to ask for clarification"""
        
        query_lower = enhanced_query.lower()
        
        # Check for pronouns without context
        if (any(pronoun in query_lower for pronoun in ["he", "his", "him"]) and not state.last_player):
            return "🤔 **Which player are you asking about?** I'd be happy to get their stats once you let me know!"
        
        # Check for very vague requests
        if query_lower.strip() in ["stats", "numbers", "performance", "show me stats", "more"]:
            if state.last_player:
                return f"📊 **What specific stats would you like to see for {state.last_player}?**\n(passing yards, touchdowns, rushing stats, career totals, etc.)"
            else:
                return "📊 **What specific stats would you like to see and for which player?**"
        
        return None
    
    def _enhance_response(self, basic_response: str, sports_response: Dict[str, Any], 
                         query_context: QueryContext, state: ConversationState) -> str:
        """Enhance the response with conversational intelligence"""
        
        enhanced_parts = [basic_response]
        
        # Add insights based on the data
        insights = self._generate_insights(sports_response, query_context, state)
        if insights:
            enhanced_parts.append("\n" + "\n".join(insights))
        
        # Add intelligent follow-up suggestions
        follow_ups = self._generate_follow_ups(sports_response, query_context, state)
        if follow_ups:
            enhanced_parts.append("\n🤔 **What's next?**")
            enhanced_parts.extend([f"• {suggestion}" for suggestion in follow_ups[:3]])
        
        # Add conversation context awareness
        if state.query_count > 1:
            context_note = self._generate_context_note(state)
            if context_note:
                enhanced_parts.append(f"\n💡 *{context_note}*")
        
        return "\n".join(enhanced_parts)
    
    def _generate_insights(self, sports_response: Dict[str, Any], 
                          query_context: QueryContext, state: ConversationState) -> List[str]:
        """Generate intelligent insights about the data"""
        
        insights = []
        
        # Insights for comparison results
        if "comparison" in sports_response:
            comparison = sports_response["comparison"]
            players = sports_response.get("players", [])
            
            if len(players) == 2:
                insights.append("💡 **Fascinating matchup!** These players have very different playing styles.")
        
        # Insights for leaderboard results
        elif "leaders" in sports_response:
            leaders = sports_response.get("leaders", [])
            
            if leaders and len(leaders) > 0:
                insights.append("🔥 **Elite performance!** These are the top performers in the league!")
        
        # Insights for single player stats
        else:
            player_name = sports_response.get("player_fullName", "")
            if player_name:
                insights.append(f"🌟 **{player_name}** shows some impressive numbers!")
        
        return insights
    
    def _generate_follow_ups(self, sports_response: Dict[str, Any], 
                           query_context: QueryContext, state: ConversationState) -> List[str]:
        """Generate intelligent follow-up suggestions"""
        
        follow_ups = []
        
        # Follow-ups for comparison results
        if "comparison" in sports_response:
            players = sports_response.get("players", [])
            if len(players) >= 2:
                follow_ups.extend([
                    f"Compare their career progression over the years",
                    f"How do they rank among all-time greats?"
                ])
        
        # Follow-ups for leaderboard results
        elif "leaders" in sports_response:
            stat = sports_response.get("ranked_stat", "")
            follow_ups.extend([
                f"Show all-time leaders in {stat}",
                f"Compare {stat} across different positions"
            ])
        
        # Follow-ups for individual player stats
        else:
            player_name = sports_response.get("player_fullName", "")
            if player_name:
                follow_ups.extend([
                    f"Compare {player_name} to other players at his position",
                    f"Show {player_name}'s career progression"
                ])
        
        return follow_ups
    
    def _generate_context_note(self, state: ConversationState) -> Optional[str]:
        """Generate a context awareness note"""
        
        if state.query_count >= 3 and state.last_player:
            return f"I can see you're really interested in {state.last_player} - I have lots more data to explore!"
        
        if len(state.favorite_players) >= 2:
            recent_players = ", ".join(state.favorite_players[-2:])
            return f"You've been exploring {recent_players} - great choices for analysis!"
        
        return None
    
    def _update_conversation_state(self, query_context: QueryContext, 
                                  sports_response: Dict[str, Any], state: ConversationState):
        """Update conversation state with new information"""
        
        # Track mentioned players
        if query_context.player_names:
            state.last_player = query_context.player_names[0]
            console.print(f"[dim green]📝 Remembering player: {state.last_player}[/dim green]")
            
            # Add to favorites (avoid duplicates)
            for player in query_context.player_names:
                if player not in state.favorite_players:
                    state.favorite_players.append(player)
        
        # Track other context
        if query_context.team_names:
            state.last_team = query_context.team_names[0]
        
        if query_context.stat_type:
            state.last_stat_type = query_context.stat_type
        
        if query_context.sport:
            state.last_sport = query_context.sport
    
    def _log_interaction(self, user_query: str, bot_response: str, state: ConversationState):
        """Log the interaction"""
        
        if self.memory:
            try:
                self.memory.chat_memory.add_user_message(user_query)
                self.memory.chat_memory.add_ai_message(bot_response)
            except Exception as e:
                console.print(f"[dim yellow]Memory logging failed: {e}[/dim yellow]")
    
    def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """Get detailed conversation statistics for a user"""
        
        if user_id not in self.conversation_states:
            return {"error": "No conversation found for this user"}
        
        state = self.conversation_states[user_id]
        
        return {
            "user_id": user_id,
            "session_id": state.session_id,
            "query_count": state.query_count,
            "favorite_players": state.favorite_players,
            "last_context": {
                "player": state.last_player,
                "team": state.last_team,
                "stat_type": state.last_stat_type,
                "sport": state.last_sport
            },
            "memory_available": self.memory is not None,
            "langchain_available": LANGCHAIN_AVAILABLE
        }
    
    def reset_conversation(self, user_id: str):
        """Reset conversation state for a user"""
        
        if user_id in self.conversation_states:
            del self.conversation_states[user_id]
        
        if self.memory:
            self.memory.clear()
        
        console.print(f"[green]🔄 Conversation reset for {user_id}[/green]")

# Global instance for easy access
conversational_bot = ConversationalSportsBot()

async def process_conversational_query(user_query: str, user_id: str = "default_user") -> str:
    """Main function to process conversational queries"""
    return await conversational_bot.process_conversation(user_query, user_id)
