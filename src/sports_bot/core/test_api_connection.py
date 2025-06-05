"""
Test script to verify API connection and key validity.
"""

import os
import sys
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv
import requests

console = Console()

def test_api_connection():
    """Test the API connection and key validity."""
    console.print(Panel("[bold blue]NFL API Connection Test[/bold blue]"))
    
    # 1. Check if .env file exists
    if not os.path.exists('.env'):
        console.print("[red]❌ .env file not found![/red]")
        console.print("Please create a .env file in the project root with your API key:")
        console.print("RAPIDAPI_KEY=your_api_key_here")
        return False
    
    # 2. Load environment variables
    load_dotenv()
    api_key = os.getenv('RAPIDAPI_KEY')
    
    if not api_key:
        console.print("[red]❌ RAPIDAPI_KEY not found in .env file![/red]")
        return False
    
    if api_key == "your_api_key_here":
        console.print("[red]❌ Please replace the default API key with your actual key in .env![/red]")
        return False
    
    # 3. Test API endpoints
    headers = {
        'X-RapidAPI-Key': api_key,
        'X-RapidAPI-Host': 'nfl-api-data.p.rapidapi.com'
    }
    
    endpoints_to_test = [
        ('Teams List', 'nfl-team-listing/v1/data'),
        ('Player Info', 'nfl-player-info/v1/data?id=3916387'),  # Test with a known player ID
        ('Team Info', 'nfl-team-info/v1/data?id=1'),  # Test with a known team ID
    ]
    
    base_url = 'https://nfl-api-data.p.rapidapi.com/'
    all_passed = True
    
    for endpoint_name, endpoint in endpoints_to_test:
        try:
            console.print(f"\nTesting {endpoint_name}...", end="")
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            
            if response.status_code == 200:
                console.print("[green] ✓ Success![/green]")
                # Print a sample of the data
                data = response.json()
                if isinstance(data, list) and data:
                    console.print(f"Sample data: {data[0]}")
                elif isinstance(data, dict):
                    console.print(f"Sample data: {list(data.keys())}")
            else:
                console.print(f"[red] ❌ Failed! Status code: {response.status_code}[/red]")
                console.print(f"Error: {response.text}")
                all_passed = False
                
        except Exception as e:
            console.print(f"[red] ❌ Error: {str(e)}[/red]")
            all_passed = False
    
    if all_passed:
        console.print("\n[green]✅ All API tests passed! Your API key is working correctly.[/green]")
    else:
        console.print("\n[red]❌ Some API tests failed. Please check the errors above.[/red]")
    
    return all_passed

if __name__ == "__main__":
    test_api_connection() 