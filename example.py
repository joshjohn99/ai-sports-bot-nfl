"""
Example script to test the NFL API implementation.
"""

import asyncio
import os
from sports_bot.data.fetcher import NFLDataFetcher

async def main():
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
        team_details = await fetcher.get_team_details(team_id)
        print(f"Team details: {team_details}")
        
        # Get players for the team
        print(f"\nFetching players for Arizona Cardinals...")
        players = await fetcher.get_players(team_id)
        print(f"Found {len(players)} players")
        
        # Print first 5 players
        print("\nFirst 5 players:")
        for player in players[:5]:
            print(f"- {player['fullName']} ({player['position']['displayName']})")

if __name__ == "__main__":
    asyncio.run(main()) 