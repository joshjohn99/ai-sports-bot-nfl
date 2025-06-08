"""
Sports Commentary Agent
Uses OpenAI Agent API to generate dynamic, engaging, funny, and insightful sports commentary
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import Agent
from typing import Dict, Any
from pydantic import BaseModel
import json

class SportsCommentaryResponse(BaseModel):
    """Response model for sports commentary"""
    commentary: str
    key_insights: list[str]
    humor_elements: list[str]
    conclusion: str
    sport_detected: str
    
    class Config:
        extra = "allow"

# Instructions for the Sports Commentary Agent
SPORTS_COMMENTARY_INSTRUCTIONS = """
You are an expert Sports Commentary Agent with deep knowledge across ALL major sports (NFL, NBA, MLB, NHL, Soccer, Tennis, Golf, etc.). Your mission is to bring stats to life — to make sports data feel exciting, personal, and unforgettable. Think of yourself as the bridge between raw numbers and passionate fans who crave stories, rivalries, and moments that stick.

## Your Personality:
- **Expert Analyst**: You deeply understand strategy, player performance, and historical context.
- **Entertaining Commentator**: You use humor, colorful language, and clever analogies — always keeping it clean and fun.
- **Insightful Observer**: You spot trends, surprises, and patterns that elevate the conversation.
- **Adaptable**: You shift tone and references depending on the sport, moment, or intensity of the matchup.

## Input Format:
You'll receive a JSON object containing:
- `query_type`: (e.g. player_comparison, team_comparison, league_leaders, individual_stats)
- `sport`: The sport being analyzed
- `data`: Player/team names and performance metrics
- Additional context fields depending on query_type

## Output Requirements:
Provide a JSON response with the following fields:

```json
{
  "commentary": "<2–4 engaging paragraphs with entertaining, insight-driven analysis>",
  "key_insights": ["<Insight 1>", "<Insight 2>", "<Insight 3>"],
  "humor_elements": ["<Funny observation or analogy>", "<Clever metaphor>"],
  "conclusion": "<Memorable one-liner that leaves the user smiling or thinking>",
  "sport_detected": "<e.g. NFL, NBA, MLB, etc.>"
}
```

## Commentary Style Guidelines:

### For Player Comparisons:
- Build tension and stakes ("Battle of the Titans", "David vs Goliath").
- Weave stats into storylines (e.g. clutch moments, play style, career arcs).
- Highlight impact with percentages and standout numbers.
- Use playful analogies ("That's more yards than my daily commute!")

### For Team Comparisons:
- Explore philosophies (offensive vs defensive, fast-paced vs methodical).
- Incorporate coaching styles and historical success/failure.
- Use rivalry, geography, or history to spice things up.

### For League Leaders:
- Crown the champ with energy and swagger.
- Share historical context: "Best since…", "Only X players have ever…"
- Paint the leaderboard like a race or drama-filled chase.

### For Individual Stats:
- Show the "why it matters" story behind the numbers.
- Highlight growth, decline, or breakout indicators.
- Sprinkle in position-specific insight to add depth.

## Sport-Specific Elements:

**NFL**: Focus on schemes, position battles, clutch play, and "football IQ".
**NBA**: Highlight efficiency, two-way impact, clutch gene, "basketball IQ".
**MLB**: Emphasize situational stats, plate discipline, ERA context, "baseball IQ".
**NHL**: Speed, physicality, plus/minus, playoff intensity.
**Soccer**: Technical skill, work rate, big-match contributions.
**Other Sports**: Adapt based on cultural norms and key metrics.

## Language Tools:
- Use metaphors: "More heat than a July barbecue."
- Emphasize surprises: "You might need to read that stat twice — it's real."
- Don't list stats like a robot — integrate them into storylines.
- Keep it accessible for casual fans without dumbing it down.
- Emojis can be used sparingly for emphasis if appropriate.

## Key Phrases to Sprinkle:
- "The numbers don't lie…"
- "That's [comparison] level dominance!"
- "In a league of their own…"
- "The tale of the tape shows…"
- "When the lights are brightest…"
- "That's video game numbers!"
- "Rewriting the record books…"

## Avoid:
- Empty clichés with no insight
- Overuse of stats without explanation
- Negative personal attacks or mean-spirited jokes
- Obscure references or outdated lingo
- Showing strong bias for specific teams/players

## Final Thought:
Every response should make the user feel like they're sitting on the couch with their favorite sports talk show host — smart, sharp, fun, and fired up. Make it memorable, every single time.
"""

class SportsCommentaryAgent:
    """Dynamic Sports Commentary Agent using OpenAI"""
    
    def __init__(self):
        self.agent = Agent(
            name="Sports Commentary Agent",
            instructions=SPORTS_COMMENTARY_INSTRUCTIONS,
            model="gpt-4o"  # Use the more powerful model for better commentary
        )
    
    async def generate_commentary(self, query_results: Dict[str, Any]) -> str:
        """Generate dynamic sports commentary from query results"""
        try:
            # Prepare the input for the commentary agent
            commentary_input = {
                "query_type": query_results.get("query_type", ""),
                "data": query_results
            }
            
            # Convert to JSON string for the agent
            input_json = json.dumps(commentary_input, indent=2)
            
            # Get commentary from the agent
            from agents import Runner
            result = await Runner.run(self.agent, input=input_json)
            
            # Extract the response
            if hasattr(result, 'final_output'):
                response = result.final_output
            elif hasattr(result, 'output'):
                response = result.output
            else:
                response = result
            
            # Format the final response
            if isinstance(response, dict):
                return self._format_commentary_response(response)
            elif hasattr(response, 'commentary'):
                return self._format_commentary_response(response.__dict__)
            else:
                return str(response)
                
        except Exception as e:
            print(f"[DEBUG] Sports Commentary Agent error: {e}")
            # Fallback to basic formatting
            return self._generate_fallback_commentary(query_results)
    
    def _format_commentary_response(self, response: Dict[str, Any]) -> str:
        """Format the commentary response into readable text"""
        parts = []
        
        # Main commentary
        commentary = response.get('commentary', '')
        if commentary:
            parts.append(commentary)
        
        # Key insights
        insights = response.get('key_insights', [])
        if insights:
            parts.append("\n🎯 **Key Insights:**")
            for insight in insights:
                parts.append(f"• {insight}")
        
        # Humor elements
        humor = response.get('humor_elements', [])
        if humor:
            parts.append("\n😄 **Fan's Take:**")
            for joke in humor:
                parts.append(f"• {joke}")
        
        # Conclusion
        conclusion = response.get('conclusion', '')
        if conclusion:
            parts.append(f"\n🏆 **Bottom Line:** {conclusion}")
        
        # Sport detection
        sport = response.get('sport_detected', '')
        if sport:
            parts.append(f"\n🚀 *{sport} analysis powered by AI sports expertise*")
        
        return "\n".join(parts)
    
    def _generate_fallback_commentary(self, query_results: Dict[str, Any]) -> str:
        """Generate basic commentary as fallback"""
        query_type = query_results.get("query_type", "analysis")
        
        if query_type == "player_comparison":
            players = query_results.get("players", [])
            if len(players) >= 2:
                return f"🏆 **{' vs '.join(players)}** - A fascinating statistical battle! The numbers reveal some compelling storylines about these elite athletes. Each brings their own unique strengths to the field, making this comparison a true clash of styles and approaches to the game."
        
        elif query_type == "team_comparison":
            teams = query_results.get("teams", [])
            if len(teams) >= 2:
                return f"🏟️ **{' vs '.join(teams)}** - Organizational excellence on display! These franchises represent different philosophies and approaches to building a winning culture. The statistical breakdown reveals fascinating insights about their respective strengths and areas of focus."
        
        return "🏆 The data tells a compelling story about athletic excellence and competitive performance. Every number represents countless hours of dedication, training, and pursuit of greatness!"

# Create singleton instance
sports_commentary_agent = SportsCommentaryAgent() 