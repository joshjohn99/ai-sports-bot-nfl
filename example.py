"""
Example script to test the NFL API implementation.
"""

import asyncio
import os
from dotenv import load_dotenv
from sports_bot.data.fetcher import NFLDataFetcher

async def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment variable
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        raise ValueError("RAPIDAPI_KEY environment variable not set")
    
    # Initialize fetcher
    async with NFLDataFetcher(api_key=api_key) as fetcher:
        # Get all teams
        print("\nFetching all NFL teams...")
        teams = await fetcher.get_teams()
        print(f"Found {len(teams)} teams")
        
        # Get Arizona Cardinals details (ID: 22)
        team_id = "22"
        print(f"\nFetching details for Arizona Cardinals (ID: {team_id})...")
        team_details = await fetcher.get_team_info(team_id)
        print(f"Team details: {team_details}")
        
        # Get roster for the team
        print(f"\nFetching roster for Arizona Cardinals...")
        roster = await fetcher.get_team_roster(team_id)
        
        if roster and "athletes" in roster:
            players = roster["athletes"]
            print(f"Found {len(players)} players")
            
            # Print first 5 players
            print("\nFirst 5 players:")
            for player in players[:5]:
                first_name = player.get('firstName', '')
                last_name = player.get('lastName', '')
                position = player.get('position', 'Unknown')
                jersey = player.get('jersey', 'N/A')
                print(f"- #{jersey} {first_name} {last_name} ({position})")
        else:
            print("❌ Could not fetch roster data")

if __name__ == "__main__":
    asyncio.run(main()) 