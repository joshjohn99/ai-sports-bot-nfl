#!/usr/bin/env python3
"""
Simple test script to check NBA API responses
"""

import os
import requests
import json
from dotenv import load_dotenv
from rich.console import Console
from rich.json import JSON

console = Console()
load_dotenv()

def test_nba_api():
    """Test the NBA API endpoints to see what we get back"""
    
    api_key = os.getenv('RAPIDAPI_KEY')
    
    if not api_key:
        console.print("[red]❌ RAPIDAPI_KEY not found in .env file[/red]")
        return
    
    console.print(f"[green]✅ API Key found: {api_key[:10]}...[/green]")
    
    headers = {
        'X-RapidAPI-Key': api_key,
        'X-RapidAPI-Host': 'nba-api-data.p.rapidapi.com'
    }
    
    # Test URLs
    test_urls = [
        'https://nba-api-data.p.rapidapi.com/nba-atlantic-team-list',
        'https://nba-api-data.p.rapidapi.com/nba-central-team-list',
        'https://nba-api-data.p.rapidapi.com/nba-player-stats?playerid=4869342'
    ]
    
    for url in test_urls:
        console.print(f"\n[bold blue]Testing URL: {url}[/bold blue]")
        console.print("=" * 80)
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            console.print(f"[cyan]Status Code: {response.status_code}[/cyan]")
            console.print(f"[cyan]Headers: {dict(response.headers)}[/cyan]")
            
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    console.print("[green]✅ JSON Response:[/green]")
                    
                    # Pretty print the JSON
                    console.print(JSON(json.dumps(json_data, indent=2)))
                    
                    # Show structure
                    console.print(f"\n[yellow]Response Structure:[/yellow]")
                    console.print(f"• Type: {type(json_data)}")
                    if isinstance(json_data, dict):
                        console.print(f"• Keys: {list(json_data.keys())}")
                        for key, value in json_data.items():
                            console.print(f"  - {key}: {type(value)} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                    
                except json.JSONDecodeError:
                    console.print("[red]❌ Response is not valid JSON:[/red]")
                    console.print(response.text[:500])
            
            elif response.status_code == 403:
                console.print("[red]❌ 403 Forbidden - Check your API key and subscription[/red]")
                console.print(f"Response: {response.text[:200]}")
            
            elif response.status_code == 404:
                console.print("[red]❌ 404 Not Found - URL might be incorrect[/red]")
                console.print(f"Response: {response.text[:200]}")
            
            else:
                console.print(f"[red]❌ HTTP {response.status_code}[/red]")
                console.print(f"Response: {response.text[:500]}")
        
        except requests.exceptions.Timeout:
            console.print("[red]❌ Request timed out[/red]")
        
        except requests.exceptions.RequestException as e:
            console.print(f"[red]❌ Request error: {e}[/red]")
        
        except Exception as e:
            console.print(f"[red]❌ Unexpected error: {e}[/red]")
        
        console.print("\n" + "=" * 80)

if __name__ == "__main__":
    test_nba_api()
