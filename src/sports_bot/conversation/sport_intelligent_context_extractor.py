"""
🏗️ Sport-Intelligent Context Extractor  
Scalable architecture that handles any sport intelligently
"""

class SportIntelligentContextExtractor:
    """
    Universal context extractor that adapts to any sport
    Uses LLM + sport configs for scalable intelligence
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        self.sport_configs = self._load_sport_configs()
        
    def _load_sport_configs(self):
        """Load sport-specific configurations dynamically"""
        return {
            "NFL": {
                "positions": ["QB", "RB", "WR", "TE", "K", "DEF"],
                "team_concepts": ["receiving corps", "offensive line", "secondary"],
                "key_metrics": ["passing_yards", "rushing_yards", "receiving_yards"],
                "data_sources": ["PlayerStats", "TeamStats"],
                "common_comparisons": ["team_vs_team", "position_groups", "individual_players"]
            },
            "NBA": {
                "positions": ["PG", "SG", "SF", "PF", "C"],
                "team_concepts": ["backcourt", "frontcourt", "starting five"],
                "key_metrics": ["points", "rebounds", "assists"],
                "data_sources": ["PlayerStats", "TeamStats"],
                "common_comparisons": ["team_vs_team", "position_groups", "individual_players"]
            },
            # Easily add MLB, NHL, etc...
        }
    
    async def extract_context(self, query: str):
        """Universal context extraction for any sport"""
        
        # Step 1: LLM detects sport + basic analysis
        sport_analysis = await self._analyze_sport_and_query(query)
        
        # Step 2: Route to sport-specific config
        sport_config = self.sport_configs.get(sport_analysis['sport'])
        
        # Step 3: Generic context extraction using sport config
        context = await self._extract_generic_context(query, sport_analysis, sport_config)
        
        # Step 4: Ask follow-ups if needed (generic logic)
        if context['missing_info']:
            return await self._generate_follow_up_questions(context, sport_config)
            
        return context
