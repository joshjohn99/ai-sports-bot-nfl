#!/usr/bin/env python3
"""
Test NBA team list endpoints to understand their response structure
"""

import os
import requests
import json
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.json import JSON

console = Console()
load_dotenv()

def test_team_endpoints():
    """Test NBA team list endpoints"""
    
    api_key = os.getenv('RAPIDAPI_KEY')
    
    if not api_key:
        console.print("[red]❌ RAPIDAPI_KEY not found[/red]")
        return
    
    headers = {
        'X-RapidAPI-Key': api_key,
        'X-RapidAPI-Host': 'nba-api-data.p.rapidapi.com'
    }

    # Test just one division first
    test_url = 'https://nba-api-data.p.rapidapi.com/nba-atlantic-team-list'
    
    console.print(f"[bold blue]Testing: {test_url}[/bold blue]")
    
    try:
        response = requests.get(test_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            console.print(f"[green]✅ Success! Status: {data.get('status')}[/green]")
            
            # Analyze the response structure
            if 'response' in data:
                response_data = data['response']
                console.print(f"\n[yellow]Response structure:[/yellow]")
                console.print(f"• Type: {type(response_data)}")
                console.print(f"• Keys: {list(response_data.keys())}")
                
                # Check teamList specifically
                if 'teamList' in response_data:
                    team_list = response_data['teamList']
                    console.print(f"\n[cyan]TeamList found:[/cyan]")
                    console.print(f"• Type: {type(team_list)}")
                    console.print(f"• Length: {len(team_list) if hasattr(team_list, '__len__') else 'N/A'}")
                    
                    if isinstance(team_list, list):
                        console.print(f"• Number of teams: {len(team_list)}")
                        
                        if team_list:
                            # Show first team structure
                            first_team = team_list[0]
                            console.print(f"\n[yellow]First team structure:[/yellow]")
                            console.print(f"• Type: {type(first_team)}")
                            console.print(f"• Keys: {list(first_team.keys()) if isinstance(first_team, dict) else 'Not a dict'}")
                            
                            # Show first team details
                            if isinstance(first_team, dict):
                                table = Table(title="First Team Details")
                                table.add_column("Field", style="cyan")
                                table.add_column("Value", style="green")
                                
                                for key, value in first_team.items():
                                    # Truncate long values
                                    str_value = str(value)
                                    if len(str_value) > 100:
                                        str_value = str_value[:100] + "..."
                                    table.add_row(key, str_value)
                                
                                console.print(table)
                            
                            # Show all teams briefly
                            console.print(f"\n[cyan]All teams in Atlantic division:[/cyan]")
                            for i, team in enumerate(team_list):
                                if isinstance(team, dict):
                                    name = team.get('displayName', team.get('name', f'Team_{i}'))
                                    abbr = team.get('abbreviation', 'N/A')
                                    team_id = team.get('id', 'N/A')
                                    console.print(f"  {i+1}. {name} ({abbr}) - ID: {team_id}")
                    
                    elif isinstance(team_list, dict):
                        console.print(f"• Team keys: {list(team_list.keys())}")
                        
                        # Show first few teams
                        for i, (key, team) in enumerate(team_list.items()):
                            if i >= 3:  # Show only first 3
                                console.print(f"  ... and {len(team_list) - 3} more teams")
                                break
                            name = team.get('displayName', team.get('name', key)) if isinstance(team, dict) else str(team)
                            console.print(f"  {key}: {name}")
                
                # Pretty print a small sample of the JSON
                console.print(f"\n[yellow]Sample JSON (first 500 chars):[/yellow]")
                json_str = json.dumps(data, indent=2)
                console.print(json_str[:500] + "..." if len(json_str) > 500 else json_str)
        
        else:
            console.print(f"[red]❌ HTTP {response.status_code}[/red]")
            console.print(f"Response: {response.text[:300]}")
    
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")

if __name__ == "__main__":
    test_team_endpoints()
