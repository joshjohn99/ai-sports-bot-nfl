#!/usr/bin/env python3
"""
Find more NBA player IDs to expand our database
"""

import os
import requests
from dotenv import load_dotenv
from rich.console import Console

console = Console()
load_dotenv()

def find_player_ids():
    """Try to find more player IDs from various sources"""
    
    api_key = os.getenv('RAPIDAPI_KEY')
    headers = {
        'X-RapidAPI-Key': api_key,
        'X-RapidAPI-Host': 'nba-api-free-data.p.rapidapi.com'
    }
    
    # Let's try some common player ID ranges based on your working ID (4869342)
    test_ids = [
        # Around your working ID
        '4869340', '4869341', '4869343', '4869344', '4869345',
        # Other patterns from your sample files
        '3915510', '3915512', '3915513',
        '3916385', '3916386', '3916388', '3916389',
        '3929628', '3929629', '3929631', '3929632',
        # Try some sequential IDs
        '4869350', '4869360', '4869370',
    ]
    
    console.print(f"[cyan]🔍 Testing {len(test_ids)} potential player IDs...[/cyan]")
    
    found_players = []
    
    for player_id in test_ids:
        try:
            url = f"https://nba-api-free-data.p.rapidapi.com/nba-player-stats"
            params = {'playerid': player_id}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    console.print(f"  ✅ Found player ID: {player_id}")
                    found_players.append(player_id)
                else:
                    console.print(f"  ❌ {player_id}: No data")
            else:
                console.print(f"  ❌ {player_id}: HTTP {response.status_code}")
            
        except Exception as e:
            console.print(f"  ⚠ {player_id}: {e}")
    
    console.print(f"\n[green]✅ Found {len(found_players)} valid player IDs:[/green]")
    for pid in found_players:
        console.print(f"  • {pid}")
    
    return found_players

if __name__ == "__main__":
    find_player_ids()
