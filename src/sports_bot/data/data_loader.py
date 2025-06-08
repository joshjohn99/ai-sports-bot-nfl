import os
import json
import requests
from datetime import datetime, timedelta
import time

# Assuming api_config and other relevant utilities might be imported from the project
# For now, let's assume api_config will be loaded or passed appropriately.
# from .config.api_config import api_config # Adjust path as needed if run from root
# from .core.stat_retriever import StatRetrieverApiAgent # For build_url, if used directly

# --- Configuration ---
# Base directory to store the fetched data
DATA_STORE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'daily_store')
# Example: sports_bot_beta/data/daily_store/

# Define which sports to process
SUPPORTED_SPORTS = ["NFL"] # Add "NBA", "MLB", "NHL" as needed

# Define seasons to fetch (e.g., current and last)
# This might need to be more dynamic, e.g., based on current date
SEASONS_TO_FETCH = {
    "NFL": ["2023", "2022"], # Example: last full season and previous
    # "NBA": ["2023-2024-regular", "2022-2023-regular"] 
}

# API call delay to be respectful to the API provider
API_CALL_DELAY_SECONDS = 1 


def ensure_dir(file_path):
    """Ensure directory exists for a given file path."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Also ensure the base data store directory exists
    if not os.path.exists(DATA_STORE_DIR):
        os.makedirs(DATA_STORE_DIR)

def get_api_config_for_sport(sport_code: str):
    """
    Placeholder to get API configuration. 
    In a real scenario, this would load from your api_config.py.
    For this script, we might need to temporarily define a simplified config
    or ensure api_config.py is importable.
    """
    # This is a simplified stand-in. 
    # You'll need to integrate your actual api_config.py loading mechanism here.
    # For now, let's assume api_config is globally available or passed.
    from sports_bot.config.api_config import api_config # Direct import assuming script is run from project root or PYTHONPATH is set
    if sport_code in api_config:
        return api_config[sport_code]
    else:
        print(f"Error: API configuration for sport '{sport_code}' not found.")
        return None

def build_url_for_loader(sport_conf: dict, endpoint_key: str, path_params: dict = None, query_params: dict = None) -> str:
    """
    Simplified URL builder for the loader script.
    Assumes urljoin and urlencode are available (standard libraries).
    """
    from urllib.parse import urljoin, urlencode # Ensure imports are here

    base_url = sport_conf['base_url']
    endpoint_template = sport_conf['endpoints'].get(endpoint_key, '')
    
    if not endpoint_template:
        raise ValueError(f"Endpoint key '{endpoint_key}' not found in sport config.")

    endpoint = endpoint_template
    if path_params:
        for key, value in path_params.items():
            endpoint = endpoint.replace(f"{{{key}}}", str(value))
    
    url = urljoin(base_url, endpoint.lstrip('/'))
    if query_params:
        url = f"{url}?{urlencode(query_params)}"
    return url

# --- Data Fetching Functions ---

def fetch_and_save_all_teams(sport_code: str):
    """Fetches and saves the list of all teams for a given sport."""
    print(f"Fetching all teams for {sport_code}...")
    sport_config = get_api_config_for_sport(sport_code)
    if not sport_config:
        return

    endpoint_key = 'AllTeams'
    if endpoint_key not in sport_config['endpoints']:
        print(f"Error: '{endpoint_key}' endpoint not defined for {sport_code}.")
        return

    try:
        url = build_url_for_loader(sport_config, endpoint_key)
        headers = sport_config['headers']
        
        print(f"  Requesting: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        teams_data = response.json()
        
        file_path = os.path.join(DATA_STORE_DIR, sport_code.lower(), 'all_teams.json')
        ensure_dir(file_path)
        with open(file_path, 'w') as f:
            json.dump(teams_data, f, indent=2)
        print(f"  Successfully fetched and saved all teams for {sport_code} to {file_path}")
        
        return teams_data # Return data for further processing (e.g., getting rosters)

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching all teams for {sport_code}: {e}")
    except ValueError as e:
        print(f"  Configuration error for {sport_code} AllTeams: {e}")
    except Exception as e:
        print(f"  An unexpected error occurred while fetching teams for {sport_code}: {e}")
    return None

def fetch_and_save_team_rosters(sport_code: str, teams_data: list):
    """Fetches and saves player rosters for each team in the provided teams_data."""
    print(f"Fetching team rosters for {sport_code}...")
    sport_config = get_api_config_for_sport(sport_code)
    if not sport_config:
        return

    endpoint_key = 'PlayersByTeam'
    if endpoint_key not in sport_config['endpoints']:
        print(f"Error: '{endpoint_key}' endpoint not defined for {sport_code}.")
        return

    if not isinstance(teams_data, list):
        print(f"Error: Expected teams_data to be a list, got {type(teams_data)}. Cannot fetch rosters.")
        return

    headers = sport_config['headers']
    rosters_saved_count = 0

    for i, team_entry in enumerate(teams_data):
        # Attempt to parse team_id based on common structures seen in stat_retriever.py
        team_id = None
        team_name_for_log = f"Team at index {i}"
        if isinstance(team_entry, dict) and 'team' in team_entry and isinstance(team_entry['team'], dict):
            team_detail = team_entry['team']
            team_id = team_detail.get('id')
            team_name_for_log = team_detail.get('displayName', team_detail.get('name', f"ID {team_id}"))
        elif isinstance(team_entry, dict) and 'id' in team_entry: # Simpler structure, e.g. list of team objects
            team_id = team_entry.get('id')
            team_name_for_log = team_entry.get('displayName', team_entry.get('name', f"ID {team_id}"))
        
        if not team_id:
            print(f"  Warning: Could not extract team_id for entry: {str(team_entry)[:100]}. Skipping roster fetch.")
            continue

        print(f"  Fetching roster for team: '{team_name_for_log}' (ID: {team_id}) ({i+1}/{len(teams_data)})...", end=" ")
        
        try:
            # The PlayersByTeam endpoint in the example config uses 'id' as a query param, not path param.
            url = build_url_for_loader(sport_config, endpoint_key, query_params={'id': team_id})
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            roster_data = response.json()
            
            file_path = os.path.join(DATA_STORE_DIR, sport_code.lower(), 'rosters', f"team_{team_id}.json")
            ensure_dir(file_path)
            with open(file_path, 'w') as f:
                json.dump(roster_data, f, indent=2)
            print(f"[SUCCESS] Saved to {file_path}")
            rosters_saved_count += 1
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Fetching roster for team {team_name_for_log} (ID: {team_id}): {e}")
        except ValueError as e:
            print(f"[ERROR] Configuration error for {sport_code} {endpoint_key} for team {team_name_for_log}: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error for team {team_name_for_log} (ID: {team_id}): {e}")
        finally:
            time.sleep(API_CALL_DELAY_SECONDS) # Delay after each team's roster fetch
            
    print(f"Finished fetching rosters for {sport_code}. Saved {rosters_saved_count}/{len(teams_data)} rosters.")

# Define core positions to fetch stats for (can be expanded)
# This helps reduce API calls if we don't need stats for every single player/position.
CORE_PLAYER_POSITIONS = {
    "NFL": ["QB", "RB", "WR", "TE", "FB",  # Offense
            "DE", "DT", "LB", "CB", "S", "MLB", "OLB", "ILB", "EDGE", "DL", "DB", # Defense
            "K", "P"] # Special Teams
    # Add other sports as needed
}

def fetch_and_save_player_season_stats(sport_code: str, seasons_to_fetch: list):
    """Fetches and saves season stats for players found in local roster files."""
    print(f"Fetching player season stats for {sport_code} for seasons: {seasons_to_fetch}...")
    sport_config = get_api_config_for_sport(sport_code)
    if not sport_config:
        return

    stats_endpoint_key = 'PlayerStats'
    if stats_endpoint_key not in sport_config['endpoints']:
        print(f"Error: '{stats_endpoint_key}' endpoint not defined for {sport_code}.")
        return

    rosters_dir = os.path.join(DATA_STORE_DIR, sport_code.lower(), 'rosters')
    if not os.path.exists(rosters_dir):
        print(f"Error: Rosters directory not found: {rosters_dir}")
        return

    headers = sport_config['headers']
    total_players_processed = 0
    total_stats_files_saved = 0
    
    relevant_positions = CORE_PLAYER_POSITIONS.get(sport_code, [])
    if not relevant_positions:
        print(f"Warning: No core positions defined for {sport_code}. Stats will be fetched for all players in rosters.")

    roster_files = [f for f in os.listdir(rosters_dir) if f.startswith('team_') and f.endswith('.json')]
    print(f"Found {len(roster_files)} team roster files in {rosters_dir}.")

    for roster_file_name in roster_files:
        roster_file_path = os.path.join(rosters_dir, roster_file_name)
        print(f"  Processing roster file: {roster_file_name}")
        try:
            with open(roster_file_path, 'r') as f:
                roster_api_data = json.load(f)
        except Exception as e:
            print(f"    Error loading roster data from {roster_file_name}: {e}. Skipping this roster.")
            continue

        # Extract player objects from roster_api_data (similar to stat_retriever.py)
        actual_player_objects = []
        if isinstance(roster_api_data, dict) and 'athletes' in roster_api_data and isinstance(roster_api_data['athletes'], list):
            possible_player_list_or_groups = roster_api_data['athletes']
            if possible_player_list_or_groups:
                first_item = possible_player_list_or_groups[0]
                if isinstance(first_item, dict) and 'position' in first_item and 'items' in first_item and isinstance(first_item['items'], list):
                    for group in possible_player_list_or_groups:
                        if isinstance(group, dict) and 'items' in group and isinstance(group['items'], list):
                            actual_player_objects.extend(group['items'])
                elif isinstance(first_item, dict) and ('fullName' in first_item or ('firstName' in first_item and 'lastName' in first_item)):
                    actual_player_objects = possible_player_list_or_groups
        
        if not actual_player_objects:
            print(f"    No player objects extracted from {roster_file_name}. Skipping.")
            continue
        
        print(f"    Found {len(actual_player_objects)} players in {roster_file_name}.")
        players_in_roster_to_fetch = []
        if not relevant_positions: # Fetch for all if no filter
            players_in_roster_to_fetch = actual_player_objects
        else:
            for player_data in actual_player_objects:
                if isinstance(player_data, dict):
                    position_info = player_data.get('position', {})
                    position_abbrev = position_info.get('abbreviation', 'N/A').upper()
                    if position_abbrev in relevant_positions:
                        players_in_roster_to_fetch.append(player_data)
            print(f"    Filtered to {len(players_in_roster_to_fetch)} players based on CORE_PLAYER_POSITIONS.")

        for player_data in players_in_roster_to_fetch:
            total_players_processed += 1
            player_id = player_data.get('id')
            player_name = player_data.get('fullName', player_data.get('displayName', f"ID {player_id}"))

            if not player_id:
                print(f"      Warning: Missing player ID for entry in {roster_file_name}. Skipping player.")
                continue

            for season_year in seasons_to_fetch:
                print(f"      Fetching stats for {player_name} (ID: {player_id}) for season {season_year}...", end=" ")
                try:
                    # PlayerStats endpoint expects 'id' and 'year' (which is season string) as query params
                    url = build_url_for_loader(sport_config, stats_endpoint_key, query_params={'id': player_id, 'year': season_year})
                    
                    response = requests.get(url, headers=headers, timeout=15) # Increased timeout slightly for player stats
                    response.raise_for_status()
                    player_stats_data = response.json()
                    
                    season_stats_dir = os.path.join(DATA_STORE_DIR, sport_code.lower(), 'player_stats', str(season_year))
                    file_path = os.path.join(season_stats_dir, f"player_{player_id}.json")
                    ensure_dir(file_path)
                    with open(file_path, 'w') as f:
                        json.dump(player_stats_data, f, indent=2)
                    print(f"[SUCCESS] Saved to {file_path}")
                    total_stats_files_saved += 1

                except requests.exceptions.RequestException as e:
                    print(f"[ERROR] Fetching stats for {player_name} (ID: {player_id}, Season: {season_year}): {e}")
                except ValueError as e:
                    print(f"[ERROR] Config/URL error for {player_name} (ID: {player_id}, Season: {season_year}): {e}")
                except Exception as e:
                    print(f"[ERROR] Unexpected error for {player_name} (ID: {player_id}, Season: {season_year}): {e}")
                finally:
                    time.sleep(API_CALL_DELAY_SECONDS) # Delay after each player's season stat fetch
    
    print(f"Finished fetching player stats for {sport_code}. Processed {total_players_processed} players. Saved {total_stats_files_saved} stat files.")

def main_loader():
    """Main function to orchestrate data loading."""
    print(f"Starting daily data loader at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data will be stored in: {os.path.abspath(DATA_STORE_DIR)}")

    for sport in SUPPORTED_SPORTS:
        print(f"\n--- Processing Sport: {sport} ---")
        
        # 1. Fetch and save all teams
        teams_data = fetch_and_save_all_teams(sport)
        
        if not teams_data:
            print(f"Could not fetch teams for {sport}. Skipping further processing for this sport.")
            continue
            
        # 2. For each team, fetch and save roster
        fetch_and_save_team_rosters(sport, teams_data)

        # 3. For relevant players in rosters, fetch and save season stats
        current_sport_seasons = SEASONS_TO_FETCH.get(sport)
        if current_sport_seasons:
            rosters_path = os.path.join(DATA_STORE_DIR, sport.lower(), 'rosters') # Define path to rosters
            fetch_and_save_player_season_stats(sport, current_sport_seasons)
        else:
            print(f"No seasons defined in SEASONS_TO_FETCH for {sport}. Skipping player stats fetch.")

        time.sleep(API_CALL_DELAY_SECONDS) # Delay between sports if processing multiple

    print(f"\nDaily data loader finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # This allows the script to be run directly, e.g., python -m sports_bot.data_loader
    # For this to work, ensure your project root is in PYTHONPATH or run from project root.
    # Or, if sports_bot_beta is the root and src is a subdir:
    # Add project root to sys.path if running script directly and imports are relative
    
    # Simplified path adjustment assuming script is in src/sports_bot/
    # and it needs to import from src/sports_bot/config
    # This is often handled by how you structure and run your project (e.g. using a venv and installing the package in editable mode)
    
    # If running `python src/sports_bot/data_loader.py` from `sports_bot_beta` root:
    # No sys.path manipulation needed if using `from sports_bot.config...`
    
    main_loader() 