"""
Test script to verify API connection and key validity.
"""

import os
import sys
from dotenv import load_dotenv
import requests

def test_api_connection():
    """Test the API connection and key validity."""
    print("NFL API Connection Test")
    
    # 1. Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create a .env file in the project root with your API key:")
        print("RAPIDAPI_KEY=your_api_key_here")
        return False
    
    # 2. Load environment variables
    load_dotenv()
    api_key = os.getenv('RAPIDAPI_KEY')
    
    if not api_key:
        print("❌ RAPIDAPI_KEY not found in .env file!")
        return False
    
    if api_key == "your_api_key_here":
        print("❌ Please replace the default API key with your actual key in .env!")
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
            print(f"\nTesting {endpoint_name}...", end="")
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            
            if response.status_code == 200:
                print(" ✓ Success!")
                # Print a sample of the data
                data = response.json()
                if isinstance(data, list) and data:
                    print(f"Sample data: {data[0]}")
                elif isinstance(data, dict):
                    print(f"Sample data: {list(data.keys())}")
            else:
                print(f" ❌ Failed! Status code: {response.status_code}")
                print(f"Error: {response.text}")
                all_passed = False
                
        except Exception as e:
            print(f" ❌ Error: {str(e)}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All API tests passed! Your API key is working correctly.")
    else:
        print("\n❌ Some API tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    test_api_connection() 