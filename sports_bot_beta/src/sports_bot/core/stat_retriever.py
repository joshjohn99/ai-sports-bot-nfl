# stat_retriever_agent.py
from ..config.api_config import api_config
import requests
import json
from datetime import datetime
from urllib.parse import urljoin, urlencode


class StatRetrieverApiAgent:
    def __init__(self, api_config):
        self.api_config = api_config

    def get_current_season(self, sport):
        current_year = datetime.now().year
        # If we're in the early months of the year, we're in the previous year's season
        if datetime.now().month < 8:  # Adjust this month based on when seasons typically end
            current_year -= 1
        
        if sport == "NFL":
            # NFL seasons are identified by a single year, e.g., 2023
            return str(current_year) 
        elif sport == "NBA":
            return f"{current_year}-{current_year + 1}-regular"
        elif sport == "NHL":
            return f"{current_year}-{current_year + 1}-regular"
        elif sport == "MLB":
            return f"{current_year}-regular"
        return f"{current_year}-regular"  # default format

    def build_url(self, sport: str, endpoint_key: str, path_params: dict = None, query_params: dict = None):
        sport_conf = self.api_config[sport]
        base_url = sport_conf['base_url']
        endpoint_template = sport_conf['endpoints'].get(endpoint_key, '')
        
        if not endpoint_template:
            raise ValueError(f"Endpoint key '{endpoint_key}' not found for sport '{sport}'")

        endpoint = endpoint_template
        if path_params:
            for key, value in path_params.items():
                # Ensure placeholder exists before trying to replace
                if f"{{{key}}}" in endpoint:
                    endpoint = endpoint.replace(f"{{{key}}}", str(value))
                else:
                    # If placeholder not in template, this might be an issue or intended
                    print(f"Warning: Path parameter '{key}' not found in endpoint template '{endpoint_template}'")
        
        # Ensure endpoint is a relative path before joining
        url = urljoin(base_url, endpoint.lstrip('/')) 

        if query_params:
            url = f"{url}?{urlencode(query_params)}"
            
        return url, sport_conf['headers']

    def _validate_query_requirements(self, query_context):
        """Validate that we have all required information for the query."""
        validation_errors = []
        missing_info = []
        
        # Check if sport is properly set
        if not query_context.sport or query_context.sport not in self.api_config:
            validation_errors.append("Sport not specified or not supported")
            missing_info.append("sport")
        
        # Determine query type and required information
        is_team_count_query = (
            hasattr(query_context, 'strategy') and query_context.strategy == "count_all_teams"
        ) or (
            query_context.metrics_needed and 
            any(m in ["team count", "number of teams", "all teams"] for m in query_context.metrics_needed)
        ) or (
            hasattr(query_context, 'output_expectation') and 
            query_context.output_expectation == "team_count"
        )
        
        is_player_specific_query = bool(query_context.player_names)
        
        is_general_stats_query = (
            query_context.metrics_needed and 
            not is_team_count_query and 
            not is_player_specific_query
        )
        
        # Validate based on query type
        if is_general_stats_query:
            validation_errors.append("Cannot fetch general stats without specifying a player")
            missing_info.append("player_name")
            
        if is_player_specific_query and not query_context.player_names:
            validation_errors.append("Player-specific query detected but no player names provided")
            missing_info.append("player_name")
            
        # Check for endpoint configuration
        if hasattr(query_context, 'endpoint') and query_context.endpoint:
            # Endpoint should be a key, not a full URL
            if query_context.endpoint.startswith('http'):
                validation_errors.append("Endpoint should be a predefined key, not a full URL")
                
        return validation_errors, missing_info

    def _generate_follow_up_question(self, missing_info, query_context, additional_context=None):
        """Generate appropriate follow-up questions based on missing information."""
        if additional_context and "multiple_players" in additional_context:
            matching_players = additional_context["multiple_players"]
            player_name = additional_context["player_name"]
            
            question = f"I found {len(matching_players)} players named '{player_name}'. Which one did you mean?\n"
            for i, match in enumerate(matching_players):
                question += f"  {i+1}. {match['team_name']} - {match['position']} - Jersey #{match['jersey']}\n"
            question += "\nPlease specify the team name or provide more details to help me identify the correct player."
            return question
            
        if "player_name" in missing_info:
            if query_context.metrics_needed:
                metrics_str = ", ".join(query_context.metrics_needed)
                return f"I'd be happy to help you get {metrics_str} statistics! However, I need to know which player you're asking about. Could you please specify the player's name?"
            else:
                return "I need to know which player you're asking about. Could you please specify the player's name?"
                
        if "sport" in missing_info:
            return "I need to know which sport you're asking about. Are you interested in NFL, NBA, MLB, or NHL statistics?"
            
        return "I need more information to help you with this request. Could you please be more specific?"

    def _get_player_id(self, sport: str, player_name: str):
        # Step 1: Fetch All Teams
        all_teams_endpoint_key = 'AllTeams' # /nfl-team-listing/v1/data
        all_teams_path = self.api_config[sport]['endpoints'].get(all_teams_endpoint_key)
        if not all_teams_path:
            print(f"Error: Endpoint key '{all_teams_endpoint_key}' not found for sport '{sport}'.")
            return None, None, None

        all_teams_url, headers = self.build_url(sport, all_teams_endpoint_key)
        print(f"\n_get_player_id: Fetching All Teams (endpoint '{all_teams_path}') to find '{player_name}'")
        print(f"_get_player_id: AllTeams URL: {all_teams_url}")

        try:
            response = requests.get(all_teams_url, headers=headers)
            response.raise_for_status()
            all_teams_response_data = response.json()
        except requests.HTTPError as e:
            print(f"_get_player_id: HTTP error fetching All Teams: {e}")
            print(f"_get_player_id: Response Text: {e.response.text if e.response else 'No response text'}")
            return None, None, None
        except json.JSONDecodeError as e:
            print(f"_get_player_id: JSON decode error fetching All Teams: {e.response.text if e.response else 'Error fetching data'}")
            return None, None, None

        # From user log: all_teams_response_data is a list, each item is like: {'team': {'id': '22', ...}}
        # So, all_teams_response_data itself is the list of wrapped team objects.
        if not isinstance(all_teams_response_data, list):
            print(f"_get_player_id: Warning: Expected AllTeams response to be a list, but got {type(all_teams_response_data)}.")
            print(f"_get_player_id: AllTeams Response (first 500 chars): {str(all_teams_response_data)[:500]}")
            return None, None, None
        
        teams_data_list = all_teams_response_data
        print(f"_get_player_id: Successfully fetched {len(teams_data_list)} entries from AllTeams. Iterating to get team IDs and then players...")

        players_by_team_endpoint_key = 'PlayersByTeam' # /nfl-player-listing/v1/data?id={team_id}

        # ---- START DEBUG: Print the first team_entry object ----
        if teams_data_list and not hasattr(self, '_printed_first_team_entry_sample'):
            print(f"_get_player_id: [DEBUG SAMPLE] First team_entry object from AllTeams response:")
            print(json.dumps(teams_data_list[0], indent=2)) # Print the first item from the list
            # Also print the extracted team_detail to see if parsing is okay for the first item
            if isinstance(teams_data_list[0], dict) and 'team' in teams_data_list[0]:
                 print(f"_get_player_id: [DEBUG SAMPLE] Extracted team_detail from first entry: {json.dumps(teams_data_list[0]['team'], indent=2)}")
            self._printed_first_team_entry_sample = True
        # ---- END DEBUG ----

        # Collect ALL matching players instead of returning the first
        matching_players = []

        for team_entry in teams_data_list:
            if not isinstance(team_entry, dict) or 'team' not in team_entry or not isinstance(team_entry['team'], dict):
                print(f"_get_player_id: Warning: Skipping team entry with unexpected structure: {str(team_entry)[:100]}")
                continue
            
            team_detail = team_entry['team']
            team_id = team_detail.get('id')
            team_name_for_log = team_detail.get('displayName', team_detail.get('name', f"ID {team_id}"))

            if not team_id:
                print(f"_get_player_id: Warning: Team entry missing 'id' in team_detail: {str(team_detail)[:100]}")
                continue

            # print(f"_get_player_id: Fetching players for team: {team_name_for_log} (ID: {team_id})")
            players_url, current_headers = self.build_url(sport, players_by_team_endpoint_key, query_params={'id': team_id})
            
            try:
                team_players_response = requests.get(players_url, headers=current_headers)
                team_players_response.raise_for_status()
                team_players_data = team_players_response.json() # This should be like teamreps.json
            except requests.HTTPError as e:
                print(f"_get_player_id: [ERROR] HTTP error {e.status_code} fetching players for team '{team_name_for_log}' (ID: {team_id}). Skipping team.")
                # Optionally, log e.response.text if needed for specific errors, but be mindful of log size
                # print(f"_get_player_id: [ERROR] Response text: {e.response.text if e.response else 'No response text'}")
                continue 
            except json.JSONDecodeError as e:
                print(f"_get_player_id: [ERROR] JSON decode error for team '{team_name_for_log}' (ID: {team_id}). Response: {team_players_response.text if team_players_response else 'Error fetching data'}. Skipping team.")
                continue

            if not hasattr(self, '_printed_team_player_data_sample'):
                print(f"_get_player_id: [DEBUG SAMPLE] Raw team_players_data for team '{team_name_for_log}' (ID: {team_id}):")
                print(json.dumps(team_players_data, indent=2))
                self._printed_team_player_data_sample = True

            actual_player_objects = []
            # Check if team_players_data is a dict and has an 'athletes' key which is a list (standard ESPN API pattern for rosters)
            if isinstance(team_players_data, dict) and 'athletes' in team_players_data and isinstance(team_players_data['athletes'], list):
                possible_player_list_or_groups = team_players_data['athletes']
                
                if possible_player_list_or_groups: # Ensure it's not empty
                    # Check if the first item in this list is a positional group (like Packers data)
                    # or a direct player object (like Cardinals data in teamreps.json)
                    first_item = possible_player_list_or_groups[0]
                    if isinstance(first_item, dict) and 'position' in first_item and 'items' in first_item and isinstance(first_item['items'], list):
                        print(f"_get_player_id: [INFO] Team {team_name_for_log}: Detected roster grouped by position. Extracting players from groups.")
                        for group in possible_player_list_or_groups:
                            if isinstance(group, dict) and 'items' in group and isinstance(group['items'], list):
                                actual_player_objects.extend(group['items'])
                    elif isinstance(first_item, dict) and ('fullName' in first_item or ('firstName' in first_item and 'lastName' in first_item)):
                        # Looks like a direct list of player objects
                        print(f"_get_player_id: [INFO] Team {team_name_for_log}: Detected direct list of player objects in 'athletes'.")
                        actual_player_objects = possible_player_list_or_groups
                    else:
                        print(f"_get_player_id: [WARN] Team {team_name_for_log}: 'athletes' list contains items of unexpected structure: {str(first_item)[:200]}")
                else:
                    print(f"_get_player_id: [INFO] Team {team_name_for_log}: 'athletes' list is empty.")
            else:
                print(f"_get_player_id: [WARN] Team {team_name_for_log}: 'athletes' key not found or not a list in team_players_data. Top-level type: {type(team_players_data)}")
                if isinstance(team_players_data, dict):
                    print(f"_get_player_id: Keys in team_players_data: {list(team_players_data.keys())}")
                continue # Skip this team if we can't find a list of players

            if not actual_player_objects:
                print(f"_get_player_id: [INFO] No player objects extracted for team {team_name_for_log} after parsing. Skipping team.")
                continue
            
            # print(f"_get_player_id: Team {team_name_for_log} has {len(actual_player_objects)} players. Searching for '{player_name}'.")

            for player_info in actual_player_objects: # Iterate through the unified list of player objects
                if not isinstance(player_info, dict):
                    # print(f"_get_player_id: [DEBUG] Skipping non-dict entry in athletes_list: {player_info}")
                    continue

                # ---- START DEBUG: Print player_info for Green Bay Packers ----
                if team_id == '9': # Green Bay Packers Team ID
                    print(f"_get_player_id: [GB DEBUG] Raw player_info for Packers player: {json.dumps(player_info, indent=2)}")
                # ---- END DEBUG ----

                # Attempt to get player name more robustly
                player_actual_name = player_info.get('fullName')
                if not player_actual_name:
                    first_name = player_info.get('firstName')
                    last_name = player_info.get('lastName')
                    if first_name and last_name:
                        player_actual_name = f"{first_name} {last_name}"
                
                player_actual_id = player_info.get('id')
                
                # Print comparison but don't return immediately
                # print(f"_get_player_id: [DEBUG] Comparing (Team: {team_name_for_log}, ID: {team_id}) API name: '{player_actual_name}' with target: '{player_name}'")

                if player_actual_name and player_actual_id:
                    if player_actual_name.lower() == player_name.lower():
                        # Found a match - collect it instead of returning immediately
                        position_info = player_info.get('position', {})
                        position_name = position_info.get('displayName', position_info.get('name', 'Unknown Position'))
                        
                        match_info = {
                            'player_id': player_actual_id,
                            'player_info': player_info,
                            'team_name': team_name_for_log,
                            'team_id': team_id,
                            'position': position_name,
                            'jersey': player_info.get('jersey', 'N/A')
                        }
                        matching_players.append(match_info)
                        print(f"_get_player_id: MATCH FOUND: '{player_actual_name}' (ID: {player_actual_id}) on team '{team_name_for_log}' - Position: {position_name}, Jersey: #{player_info.get('jersey', 'N/A')}")
        
        # Now handle the results
        if len(matching_players) == 0:
            print(f"_get_player_id: Warning: Player '{player_name}' not found after checking all teams.")
            return None, None, None
        elif len(matching_players) == 1:
            # Only one match - return it as before
            match = matching_players[0]
            print(f"_get_player_id: SUCCESS: Found unique player '{player_name}' (ID: {match['player_id']}) on team '{match['team_name']}'.")
            return match['player_id'], match['player_info'], match['team_name']
        else:
            # Multiple matches - return special indicator for disambiguation
            print(f"_get_player_id: MULTIPLE MATCHES: Found {len(matching_players)} players named '{player_name}':")
            for i, match in enumerate(matching_players):
                print(f"  {i+1}. {match['team_name']} - {match['position']} - Jersey #{match['jersey']}")
            
            # Return a special format to indicate multiple matches
            return "MULTIPLE_MATCHES", matching_players, None

    def get_season_format(self, sport, season_years=None):
        """Get the correct season format for the sport."""
        if season_years and len(season_years) > 0:
            year = season_years[0]
            if sport == "NFL":
                return str(year) # NFL uses single year for season
            elif sport in ["NBA", "NHL"]:
                return f"{year}-{year + 1}-regular"
            else: # MLB and default
                return f"{year}-regular"
        
        # Default to current season if no years provided
        return self.get_current_season(sport)

    def fetch_stats(self, query_context):
        # Validate query requirements first
        validation_errors, missing_info = self._validate_query_requirements(query_context)
        
        if validation_errors:
            follow_up_question = self._generate_follow_up_question(missing_info, query_context)
            return {
                "error": "Missing required information",
                "validation_errors": validation_errors,
                "follow_up_question": follow_up_question,
                "missing_info": missing_info
            }
        
        return self._fetch_stats_internal(query_context)

    def fetch_stats_with_resolved_player(self, query_context, resolved_player_id, resolved_player_info, resolved_team_name):
        """Fetch stats using pre-resolved player information to avoid re-searching."""
        # Validate basic query requirements (but skip player validation since it's resolved)
        validation_errors = []
        
        # Check if sport is properly set
        if not query_context.sport or query_context.sport not in self.api_config:
            validation_errors.append("Sport not specified or not supported")
        
        if validation_errors:
            return {
                "error": "Missing required information",
                "validation_errors": validation_errors,
                "follow_up_question": "Please specify a valid sport.",
                "missing_info": ["sport"]
            }
        
        return self._fetch_stats_internal(query_context, resolved_player_id, resolved_player_info, resolved_team_name)

    def _fetch_stats_internal(self, query_context, pre_resolved_player_id=None, pre_resolved_player_info=None, pre_resolved_team_name=None):
        """Internal method to fetch stats with optional pre-resolved player information."""
        print(f"[DEBUG] _fetch_stats_internal called with pre_resolved_player_id={pre_resolved_player_id is not None}")
        
        sport = query_context.sport
        if not sport or sport not in self.api_config:
            if sport is None and hasattr(query_context, 'output_expectation') and query_context.output_expectation == "team_count":
                print("Warning: Sport was None, defaulting to NFL for team count query.")
                sport = "NFL"
                query_context.sport = "NFL" 
            else:
                return {"error": f"Sport '{query_context.sport}' not configured or not provided."}

        is_all_teams_query = False
        if hasattr(query_context, 'strategy') and query_context.strategy == "count_all_teams":
            is_all_teams_query = True
        elif not query_context.player_names and \
             query_context.metrics_needed and \
             any(m in ["team count", "number of teams", "all teams"] for m in query_context.metrics_needed):
            is_all_teams_query = True
        elif not query_context.player_names and \
             hasattr(query_context, 'output_expectation') and query_context.output_expectation == "team_count":
            is_all_teams_query = True
        
        if is_all_teams_query:
            all_teams_endpoint_key = 'AllTeams' 
            endpoint_path = self.api_config[sport]['endpoints'].get(all_teams_endpoint_key)
            if not endpoint_path:
                return {"error": f"Endpoint key '{all_teams_endpoint_key}' not found for sport '{sport}'."}

            url, headers = self.build_url(sport, all_teams_endpoint_key)
            print(f"\nFetching All Teams Data (for counting):")
            print(f"URL: {url}")

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                all_teams_data = response.json()
            except requests.HTTPError as e:
                print(f"HTTP error fetching All Teams for count: {e}")
                return {"error": f"API error fetching all teams: {e.response.text if e.response else 'Failed to fetch'}"}
            except json.JSONDecodeError as e:
                print(f"JSON decode error fetching All Teams for count: {e.response.text if e.response else 'Error fetching data'}")
                return {"error": "Failed to decode all teams response."}

            teams_list = None
            if isinstance(all_teams_data, list):
                teams_list = all_teams_data
            elif isinstance(all_teams_data, dict):
                possible_keys = ['teams', 'body', 'results', 'data', 'teamListing', 'listing', 'league', 'conferences'] 
                for key in possible_keys:
                    if key in all_teams_data and isinstance(all_teams_data[key], list):
                        teams_list = all_teams_data[key]
                        break
                if not teams_list and 'league' in all_teams_data and isinstance(all_teams_data['league'], dict):
                    league_data = all_teams_data['league']
                    if 'conferences' in league_data and isinstance(league_data['conferences'], list):
                        temp_teams = []
                        for conf in league_data['conferences']:
                            if isinstance(conf, dict) and 'teams' in conf and isinstance(conf['teams'], list):
                                temp_teams.extend(conf['teams'])
                        if temp_teams: teams_list = temp_teams
                    elif 'teams' in league_data and isinstance(league_data['teams'], list):
                         teams_list = league_data['teams']
            
            if teams_list is not None:
                num_teams = len(teams_list)
                print(f"Successfully fetched and counted {num_teams} teams.")
                return {"query": query_context.question, "sport": sport, "number_of_teams": num_teams, "raw_data_preview": str(all_teams_data)[:1000]}
            else:
                print(f"Warning: Could not find a list of teams in the response from {url}.")
                print(f"AllTeams Response (first 500 chars): {str(all_teams_data)[:500]}")
                return {"error": "Could not determine team count from API response.", "raw_response": str(all_teams_data)[:500]}
        
        else: # Player-specific stats flow
            # Use pre-resolved player info if provided, otherwise look up the player
            if pre_resolved_player_id and pre_resolved_player_info and pre_resolved_team_name:
                print(f"[DEBUG] Using PRE-RESOLVED player data - avoiding search")
                player_id = pre_resolved_player_id
                player_info_from_roster = pre_resolved_player_info
                team_name_player_found_on = pre_resolved_team_name
                print(f"Using pre-resolved Player ID: {player_id} for {player_info_from_roster.get('fullName')}. Found on team: {team_name_player_found_on}")
            else:
                print(f"[DEBUG] No pre-resolved data - will search for player")
                player_id = None
                player_info_from_roster = None
                team_name_player_found_on = None

                if query_context.player_names:
                    player_name = query_context.player_names[0] 
                    print(f"[DEBUG] Starting player search for: {player_name}")
                    player_id, player_info_from_roster, team_name_player_found_on = self._get_player_id(sport, player_name)
                    
                    # Handle multiple matches
                    if player_id == "MULTIPLE_MATCHES":
                        matching_players = player_info_from_roster  # In this case, it contains the list of matches
                        follow_up_question = self._generate_follow_up_question(
                            [], 
                            query_context, 
                            additional_context={
                                "multiple_players": matching_players,
                                "player_name": player_name
                            }
                        )
                        return {
                            "error": "Multiple players found",
                            "follow_up_question": follow_up_question,
                            "matching_players": matching_players,
                            "player_name": player_name
                        }
                    
                    if not player_id:
                        return {"error": f"Player ID for {player_name} not found or error during fetch."}
                    print(f"Retrieved Player ID: {player_id} for {player_name}. Found on team: {team_name_player_found_on}")

            # Check if the query is specifically for team affiliation
            # NLU should set metrics_needed to something like ['team'], ['team affiliation'], ['current team']
            # or output_expectation to 'team_info', 'player_team'
            is_team_affiliation_query = False
            if query_context.metrics_needed and \
               any(m.lower() in ['team', 'team affiliation', 'current team', 'team name'] for m in query_context.metrics_needed):
                is_team_affiliation_query = True
            elif hasattr(query_context, 'output_expectation') and query_context.output_expectation and \
                 query_context.output_expectation.lower() in ['team_info', 'player_team', 'team_name']:
                is_team_affiliation_query = True

            if is_team_affiliation_query and player_id and player_info_from_roster and team_name_player_found_on:
                print(f"StatRetriever: [INFO] Query is for team affiliation. Returning info for {player_info_from_roster.get('fullName')}.")
                return {
                    "player_id": player_id,
                    "player_fullName": player_info_from_roster.get('fullName'),
                    "team_name": team_name_player_found_on,
                    "team_id": player_info_from_roster.get('team', {}).get('id'), # If team is part of player_info
                    "brief_player_info": player_info_from_roster # Contains basic details from roster
                }

            # Determine endpoint_key for stats fetching
            temp_endpoint_key = query_context.endpoint # Get what QueryPlanner might have set

            if temp_endpoint_key and temp_endpoint_key in self.api_config[sport]['endpoints']:
                endpoint_key = temp_endpoint_key
                print(f"StatRetriever: Using endpoint_key from QueryContext: {endpoint_key}")
            elif player_id: # If we have a player_id, and no valid endpoint was provided by QP
                # If query was about team affiliation, we would have returned already.
                # So, if we are here with a player_id, it implies a need for player stats or details.
                # We need a way for NLU/QP to hint if PlayerDetails is preferred over PlayerStats.
                # For now, if metrics_needed is empty (e.g. "which team" or general info), 
                # and it wasn't a team_affiliation_query, let's try PlayerDetails.
                # Otherwise, default to PlayerStats for specific metrics.
                if not query_context.metrics_needed and hasattr(query_context, 'output_expectation') and query_context.output_expectation and query_context.output_expectation in ['player_info', 'summary']:
                    endpoint_key = "PlayerDetails"
                    print(f"StatRetriever: Defaulting endpoint_key to PlayerDetails for player ID {player_id} (general info query)")
                else:
                    endpoint_key = "PlayerStats" # Default for player-specific stats when metrics are expected
                    print(f"StatRetriever: Defaulting endpoint_key to PlayerStats for player ID {player_id} (stats query)")
            else:
                return {"error": "Cannot determine API endpoint: No player context or valid predefined endpoint key provided, and not a recognized general query."}
            
            # Final check that endpoint_key is valid before proceeding
            if endpoint_key not in self.api_config[sport]['endpoints']:
                print(f"StatRetriever: [FATAL] Determined endpoint_key '{endpoint_key}' is not a valid key in api_config. QueryContext.endpoint was likely invalid: {query_context.endpoint}")
                return {"error": f"Internal error: Invalid endpoint key '{endpoint_key}' determined."}

            # Ensure player_id exists if the determined endpoint_key requires it (like PlayerStats)
            if endpoint_key == "PlayerStats" and not player_id:
                 return {"error": f"Player ID required for {endpoint_key} endpoint but not found."}

            season = self.get_season_format(sport, query_context.season_years)
            query_params = {}
            if endpoint_key == "PlayerStats":
                if not player_id: # Should have been caught above, but defensive check
                     return {"error": "Player ID required for PlayerStats endpoint but not found."}
                query_params['id'] = player_id
                season = self.get_season_format(sport, query_context.season_years)
                if not season:
                     return {"error": "Could not determine season for PlayerStats API query."}
                query_params['year'] = season
            elif endpoint_key == "PlayerDetails": # Handling for the PlayerDetails endpoint
                if not player_id:
                     return {"error": "Player ID required for PlayerDetails endpoint but not found."}
                query_params['id'] = player_id
            # Add other endpoint_key specific parameter logic here if needed

            url, headers = self.build_url(sport, endpoint_key, query_params=query_params)
            print(f"\nAPI Request Details (for {endpoint_key}):")
            print(f"URL: {url}")
            print(f"Query Params: {query_params}")

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
            except requests.HTTPError as e:
                error_text = e.response.text if e.response else 'Failed to fetch stats'
                print(f"Warning: HTTP error during {endpoint_key} fetch: {e.status_code} - {error_text}")
                return {"error": f"API error {e.status_code}: {error_text}"}
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON response from {endpoint_key} fetch: {e}")
                return {"error": f"Failed to decode {endpoint_key} response."}

            print("\n--- Raw API Data ---")
            full_response_json = json.dumps(data, indent=2)
            if len(full_response_json) > 2000:
                print(f"{full_response_json[:2000]}...\n[TRUNCATED - Full response saved to file]")
            else:
                print(full_response_json)
            
            # Save response to file for examination
            try:
                response_filename = f"api_response_{endpoint_key}_{player_id if player_id else 'unknown'}.json"
                with open(response_filename, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"\n[DEBUG] API response saved to: {response_filename}")
            except Exception as e:
                print(f"[DEBUG] Could not save response to file: {e}")
            
            # Debug: Print the top-level structure
            print(f"\n[DEBUG] API Response Analysis:")
            print(f"[DEBUG] Response type: {type(data)}")
            print(f"[DEBUG] Top-level keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Look for statistics structure
            if isinstance(data, dict) and 'statistics' in data:
                stats_data = data['statistics']
                print(f"[DEBUG] Statistics type: {type(stats_data)}")
                print(f"[DEBUG] Statistics keys: {list(stats_data.keys()) if isinstance(stats_data, dict) else 'Not a dict'}")
                
                if isinstance(stats_data, dict) and 'splits' in stats_data:
                    splits = stats_data['splits']
                    print(f"[DEBUG] Splits type: {type(splits)}")
                    print(f"[DEBUG] Number of splits: {len(splits) if isinstance(splits, list) else 'Not a list'}")
                    
                    if isinstance(splits, list) and len(splits) > 0:
                        first_split = splits[0]
                        print(f"[DEBUG] First split type: {type(first_split)}")
                        print(f"[DEBUG] First split keys: {list(first_split.keys()) if isinstance(first_split, dict) else 'Not a dict'}")
            else:
                print(f"[DEBUG] No 'statistics' key found in response")
                
                # Check for alternative structures
                if isinstance(data, dict):
                    # Look for other potential stat containers
                    potential_stat_keys = ['stats', 'playerStats', 'seasonStats', 'career', 'totals', 'data']
                    for key in potential_stat_keys:
                        if key in data:
                            print(f"[DEBUG] Found alternative stats key: '{key}' - type: {type(data[key])}")
                            if isinstance(data[key], dict):
                                print(f"[DEBUG] Keys in '{key}': {list(data[key].keys())}")
                            elif isinstance(data[key], list) and len(data[key]) > 0:
                                print(f"[DEBUG] First item in '{key}' list: {type(data[key][0])}")
                                if isinstance(data[key][0], dict):
                                    print(f"[DEBUG] Keys in first '{key}' item: {list(data[key][0].keys())}")
            
            # --- Start of new stats extraction logic ---
            extracted_stats = {}
            if hasattr(query_context, 'metrics_needed') and query_context.metrics_needed:
                print(f"\n[DEBUG] Attempting schema-based stats extraction...")
                
                # Try the new schema-based extraction first
                extracted_stats = self.extract_stats_using_schema(data, query_context.metrics_needed, sport)
                
                if extracted_stats and any(stat.get('value') != "Not found" for stat in extracted_stats.values()):
                    print(f"[SUCCESS] Schema-based extraction found {len(extracted_stats)} metrics")
                else:
                    print(f"[FALLBACK] Schema extraction failed, trying legacy method...")
                    # Fall back to the legacy extraction method if schema fails
                    extracted_stats = self._legacy_stats_extraction(data, query_context, sport)
            # --- End of new stats extraction logic ---
            
            # Construct a cleaner response object
            player_data_from_stats = data.get("player", {}) # Data from PlayerStats API call
            final_query_year_str = str(self.get_season_format(sport, query_context.season_years)) # Target year as string

            final_response_payload = {
                "player_id": player_id, # From _get_player_id
                "player_fullName": player_info_from_roster.get('fullName') if player_info_from_roster else player_data_from_stats.get("fullName"),
                "player_team_name": team_name_player_found_on, # From _get_player_id
                "season": final_query_year_str,
                "sport": sport
            }
            
            # Add extracted stats to response (handle both new and legacy formats)
            if extracted_stats:
                for metric_name, metric_data in extracted_stats.items():
                    if isinstance(metric_data, dict) and 'value' in metric_data:
                        # New schema-based format with metadata
                        final_response_payload[metric_name] = {
                            'value': metric_data['value'],
                            'displayValue': metric_data.get('displayValue', str(metric_data['value'])),
                            'standardizedName': metric_data.get('standardizedName', metric_name),
                            'displayName': metric_data.get('displayName', metric_name),
                            'category': metric_data.get('category', 'unknown'),
                            'rank': metric_data.get('rank'),
                            'abbreviation': metric_data.get('abbreviation', ''),
                            'aggregatable': metric_data.get('aggregatable', False)
                        }
                    else:
                        # Legacy format (simple value)
                        final_response_payload[metric_name] = metric_data
                        
                # Create a summary for easy access
                simple_stats = {}
                for metric_name, metric_data in extracted_stats.items():
                    if isinstance(metric_data, dict) and 'value' in metric_data:
                        simple_stats[metric_name] = metric_data['value']
                    else:
                        simple_stats[metric_name] = metric_data
                final_response_payload['simple_stats'] = simple_stats
                
                print(f"\nStatRetriever: Final Response with Stats:")
                for metric, value in simple_stats.items():
                    print(f"  {metric}: {value}")
            else:
                print(f"\nStatRetriever: No metrics were requested or found")
                
            return final_response_payload

    def retrieve_stats(self, sport, endpoint_key, path_params=None, query_params=None, **kwargs):
        if kwargs:
            if query_params is None: query_params = {}
            query_params.update(kwargs)

        url, headers = self.build_url(sport, endpoint_key, path_params=path_params, query_params=query_params)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} {response.text}")
        return response.json()

    def _normalize_metric_for_matching(self, user_metric, api_names_list):
        """
        Intelligent matching between user input and API metric names using the NFLStatsSchema.
        Handles singular/plural, abbreviations, and common variations.
        Returns the best matching API name or None.
        """
        user_metric_lower = user_metric.lower().replace(" ", "").replace("_", "").replace("-", "")
        print(f"[DEBUG] Matching '{user_metric}' (normalized: '{user_metric_lower}') against: {api_names_list}")
        
        # First try the schema-based matching
        schema_match = NFLStatsSchema.find_stat_by_user_term(user_metric)
        if schema_match and schema_match in api_names_list:
            print(f"[DEBUG] Schema match found: '{user_metric}' -> '{schema_match}'")
            return schema_match
        
        # Create normalized versions of API names for comparison
        api_names_normalized = [(name.lower().replace(" ", "").replace("_", "").replace("-", ""), name) for name in api_names_list]
        print(f"[DEBUG] Normalized API names: {[norm for norm, orig in api_names_normalized]}")
        
        # Direct match
        for normalized_api, original_api in api_names_normalized:
            if user_metric_lower == normalized_api:
                print(f"[DEBUG] Direct match found: '{user_metric}' -> '{original_api}'")
                return original_api
        
        # Try the original flexible matching as fallback (simplified)
        metric_variations = {
            # Basic singular/plural variations
            'sack': ['sacks'],
            'sacks': ['sacks'],
            'tackle': ['tackles', 'totaltackles'],
            'tackles': ['tackles', 'totaltackles'],
            'interception': ['interceptions'],
            'interceptions': ['interceptions'],
            'touchdown': ['touchdowns', 'totaltouchdowns'],
            'touchdowns': ['touchdowns', 'totaltouchdowns'],
            'td': ['touchdowns', 'totaltouchdowns'],
            'tds': ['touchdowns', 'totaltouchdowns'],
        }
        
        # Check variations
        if user_metric_lower in metric_variations:
            possible_matches = metric_variations[user_metric_lower]
            print(f"[DEBUG] Found variations for '{user_metric}': {possible_matches}")
            for possible_match in possible_matches:
                for normalized_api, original_api in api_names_normalized:
                    if possible_match == normalized_api:
                        print(f"[DEBUG] Variation match found: '{user_metric}' -> '{possible_match}' -> '{original_api}'")
                        return original_api
        
        # Partial matching - if user metric is contained in API name or vice versa
        for normalized_api, original_api in api_names_normalized:
            if user_metric_lower in normalized_api or normalized_api in user_metric_lower:
                # Additional check for meaningful partial matches (avoid very short matches)
                if len(user_metric_lower) >= 3 and len(normalized_api) >= 3:
                    print(f"[DEBUG] Partial match found: '{user_metric}' <-> '{original_api}'")
                    return original_api
        
        # No match found
        print(f"[DEBUG] No match found for '{user_metric}'")
        return None

    def extract_stats_using_schema(self, data, requested_metrics, sport='NFL'):
        """
        Extract statistics using the NFLStatsSchema for standardized results.
        Returns a dictionary with standardized stat names and values.
        """
        extracted_stats = {}
        
        if sport != 'NFL':
            print(f"[WARNING] Schema-based extraction only available for NFL. Got: {sport}")
            return extracted_stats
        
        print(f"\n[DEBUG] Schema-based extraction for metrics: {requested_metrics}")
        
        # Get statistics structure
        stats_data = data.get('statistics', {})
        if not isinstance(stats_data, dict):
            print(f"[ERROR] No valid statistics structure found")
            return extracted_stats
            
        splits = stats_data.get('splits', {})
        if not isinstance(splits, dict):
            print(f"[ERROR] No valid splits structure found")
            return extracted_stats
            
        categories = splits.get('categories', [])
        if not isinstance(categories, list):
            print(f"[ERROR] No valid categories found")
            return extracted_stats
        
        # Build a lookup map from the API response
        stat_lookup = {}
        for category in categories:
            if not isinstance(category, dict):
                continue
                
            category_name = category.get('name', '')
            stats_list = category.get('stats', [])
            
            for stat_item in stats_list:
                if isinstance(stat_item, dict):
                    stat_name = stat_item.get('name')
                    stat_value = stat_item.get('value')
                    if stat_name and stat_value is not None:
                        stat_lookup[stat_name] = {
                            'value': stat_value,
                            'displayValue': stat_item.get('displayValue', str(stat_value)),
                            'category': category_name,
                            'rank': stat_item.get('rank'),
                            'description': stat_item.get('description', '')
                        }
        
        print(f"[DEBUG] Built stat lookup with {len(stat_lookup)} stats")
        
        # Extract requested metrics using schema
        for user_metric in requested_metrics:
            # Try to find the metric using schema
            schema_stat_name = NFLStatsSchema.find_stat_by_user_term(user_metric)
            
            if schema_stat_name and schema_stat_name in stat_lookup:
                stat_info = stat_lookup[schema_stat_name]
                schema_info = NFLStatsSchema.get_stat_info(schema_stat_name)
                
                extracted_stats[user_metric] = {
                    'value': stat_info['value'],
                    'displayValue': stat_info['displayValue'],
                    'standardizedName': schema_stat_name,
                    'displayName': schema_info.get('display_name', schema_stat_name),
                    'category': stat_info['category'],
                    'rank': stat_info.get('rank'),
                    'description': stat_info.get('description', schema_info.get('description', '')),
                    'abbreviation': schema_info.get('abbreviation', ''),
                    'aggregatable': schema_info.get('aggregatable', False)
                }
                print(f"[INFO] Schema extraction: '{user_metric}' -> '{schema_stat_name}' = {stat_info['value']}")
            else:
                # Fallback to direct lookup if no schema match
                if user_metric in stat_lookup:
                    stat_info = stat_lookup[user_metric]
                    extracted_stats[user_metric] = {
                        'value': stat_info['value'],
                        'displayValue': stat_info['displayValue'],
                        'standardizedName': user_metric,
                        'displayName': user_metric,
                        'category': stat_info['category'],
                        'rank': stat_info.get('rank'),
                        'description': stat_info.get('description', ''),
                        'abbreviation': '',
                        'aggregatable': True  # Assume aggregatable unless specified otherwise
                    }
                    print(f"[INFO] Direct extraction: '{user_metric}' = {stat_info['value']}")
                else:
                    extracted_stats[user_metric] = {
                        'value': "Not found",
                        'displayValue': "Not found",
                        'standardizedName': user_metric,
                        'displayName': user_metric,
                        'category': 'unknown',
                        'rank': None,
                        'description': 'Statistic not found in API response',
                        'abbreviation': '',
                        'aggregatable': False
                    }
                    print(f"[WARNING] Could not find: '{user_metric}'")
        
        return extracted_stats

    def _legacy_stats_extraction(self, data, query_context, sport):
        """Legacy stats extraction method as fallback."""
        extracted_stats = {}
        try:
            print(f"\n[DEBUG] Looking for metrics: {query_context.metrics_needed}")
            stats_splits = data.get('statistics', {}).get('splits', [])
            print(f"[DEBUG] Found {len(stats_splits)} stats splits")
            
            categories_to_search = []
            if isinstance(stats_splits, list) and len(stats_splits) > 0 and isinstance(stats_splits[0], dict):
                categories_to_search = stats_splits[0].get('categories', [])
                print(f"[DEBUG] Found {len(categories_to_search)} categories in first split")
            
            if not isinstance(categories_to_search, list):
                print(f"StatRetriever: [WARN] Expected 'categories' to be a list, got {type(categories_to_search)}")
                categories_to_search = []

            for metric_needed in query_context.metrics_needed:
                found_metric_value = "Not found in API response structure"
                processed_for_this_metric = False

                # First, try the 'scoring' category as it has direct name-value pairs and often key TD stats
                for category in categories_to_search:
                    if isinstance(category, dict) and category.get('name') == 'scoring' and \
                       'stats' in category and isinstance(category['stats'], list):
                        # Use intelligent matching for scoring category
                        scoring_stat_names = [stat_item.get('name', '') for stat_item in category['stats'] if isinstance(stat_item, dict)]
                        matched_api_name = self._normalize_metric_for_matching(metric_needed, scoring_stat_names)
                        
                        if matched_api_name:
                            for stat_item in category['stats']:
                                if isinstance(stat_item, dict) and stat_item.get('name') == matched_api_name:
                                    found_metric_value = stat_item.get('value')
                                    processed_for_this_metric = True
                                    break
                    if processed_for_this_metric: break

                # If not found in 'scoring' or if it's not a TD-like query, try other categories by index
                if not processed_for_this_metric:
                    for category in categories_to_search:
                        if isinstance(category, dict) and \
                           'names' in category and isinstance(category['names'], list) and \
                           'statistics' in category and isinstance(category['statistics'], list):
                            
                            # Use intelligent matching for category names
                            matched_api_name = self._normalize_metric_for_matching(metric_needed, category['names'])
                            
                            if matched_api_name:
                                try:
                                    # Find the index of the matched API name
                                    metric_idx = category['names'].index(matched_api_name)
                                    
                                    # Find the stats for the correct season year
                                    target_season = str(self.get_season_format(sport, query_context.season_years))
                                    
                                    for season_stats_entry in category['statistics']:
                                        if isinstance(season_stats_entry, dict):
                                            entry_season = str(season_stats_entry.get('season', {}).get('year', 'unknown'))
                                            if entry_season == target_season:
                                                stats_values_list = season_stats_entry.get('stats')
                                                if isinstance(stats_values_list, list) and metric_idx < len(stats_values_list):
                                                    found_metric_value = stats_values_list[metric_idx]
                                                    # Convert to int/float if possible, as API returns strings in this list
                                                    try:
                                                        if isinstance(found_metric_value, str) and '.' in found_metric_value:
                                                            found_metric_value = float(found_metric_value.replace(',', ''))
                                                        elif isinstance(found_metric_value, str):
                                                            found_metric_value = int(found_metric_value.replace(',', ''))
                                                    except ValueError:
                                                        pass # Keep as string if conversion fails
                                                    processed_for_this_metric = True
                                                    break 
                                except ValueError:
                                    pass
                        if processed_for_this_metric: break
                
                extracted_stats[metric_needed] = found_metric_value
                
        except Exception as e:
            print(f"StatRetriever: [ERROR] Error during legacy metrics extraction: {e}")
            for metric_needed_err in query_context.metrics_needed:
                if metric_needed_err not in extracted_stats:
                    extracted_stats[metric_needed_err] = "Error during extraction"
        
        return extracted_stats

class NFLStatsSchema:
    """
    Comprehensive mapping of NFL player statistics based on actual API response structure.
    Enables standardized access, comparisons, and aggregations.
    """
    
    # Category mappings from API response
    CATEGORIES = {
        'general': 'General Stats',
        'defensive': 'Defensive Stats', 
        'defensiveInterceptions': 'Interceptions',
        'scoring': 'Scoring Stats'
    }
    
    # Complete stats mapping with metadata
    STATS_MAPPING = {
        # General Stats
        'fumblesForced': {
            'category': 'general',
            'display_name': 'Forced Fumbles',
            'abbreviation': 'FF',
            'description': 'The total number of forced fumbles',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['forced fumbles', 'fumbles forced', 'ff']
        },
        'fumblesRecovered': {
            'category': 'general',
            'display_name': 'Fumbles Recovered',
            'abbreviation': 'FR',
            'description': 'The number of fumbles recovered',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['fumbles recovered', 'fr', 'recovered fumbles']
        },
        'fumblesRecoveredYards': {
            'category': 'general',
            'display_name': 'Fumble Recovery Yards',
            'abbreviation': 'FRYDS',
            'description': 'Yards gained after fumble recovery',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['fumble recovery yards', 'fr yards']
        },
        'fumblesTouchdowns': {
            'category': 'general',
            'display_name': 'Fumble Touchdowns',
            'abbreviation': 'FTD',
            'description': 'Fumbles recovered and returned for TD',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['fumble touchdowns', 'fumble tds', 'ftd']
        },
        'gamesPlayed': {
            'category': 'general',
            'display_name': 'Games Played',
            'abbreviation': 'GP',
            'description': 'Total games played',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['games played', 'gp', 'games']
        },
        
        # Defensive Stats
        'assistTackles': {
            'category': 'defensive',
            'display_name': 'Assist Tackles',
            'abbreviation': 'AST',
            'description': 'Number of assist tackles',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['assist tackles', 'assists', 'ast']
        },
        'soloTackles': {
            'category': 'defensive', 
            'display_name': 'Solo Tackles',
            'abbreviation': 'SOLO',
            'description': 'Number of solo tackles',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['solo tackles', 'solo', 'unassisted tackles']
        },
        'totalTackles': {
            'category': 'defensive',
            'display_name': 'Total Tackles',
            'abbreviation': 'TOT',
            'description': 'Total tackles (solo + assists)',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['total tackles', 'tackles', 'tot', 'combined tackles']
        },
        'sacks': {
            'category': 'defensive',
            'display_name': 'Sacks',
            'abbreviation': 'SACK',
            'description': 'Total number of sacks',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['sacks', 'sack', 'qb sacks']
        },
        'sackYards': {
            'category': 'defensive',
            'display_name': 'Sack Yards',
            'abbreviation': 'SCKYDS',
            'description': 'Yards lost from sacks',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['sack yards', 'sack yardage']
        },
        'QBHits': {
            'category': 'defensive',
            'display_name': 'QB Hits',
            'abbreviation': 'QB HTS',
            'description': 'Quarterback hits',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['qb hits', 'quarterback hits', 'qb pressures']
        },
        'tacklesForLoss': {
            'category': 'defensive',
            'display_name': 'Tackles For Loss',
            'abbreviation': 'TFL',
            'description': 'Tackles resulting in yardage loss',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['tackles for loss', 'tfl', 'tfl tackles']
        },
        'passesDefended': {
            'category': 'defensive',
            'display_name': 'Passes Defended',
            'abbreviation': 'PD',
            'description': 'Total passes defended',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['passes defended', 'pd', 'pass defense']
        },
        'stuffs': {
            'category': 'defensive',
            'display_name': 'Stuffs',
            'abbreviation': 'STF',
            'description': 'Runners stuffed at/behind line of scrimmage',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['stuffs', 'stf', 'stuff tackles']
        },
        'hurries': {
            'category': 'defensive',
            'display_name': 'Hurries',
            'abbreviation': 'HUR',
            'description': 'Times quarterback was hurried',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['hurries', 'hur', 'qb hurries']
        },
        'safeties': {
            'category': 'defensive',
            'display_name': 'Safeties',
            'abbreviation': 'SAFE',
            'description': 'Safeties forced',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['safeties', 'safe', 'safety']
        },
        
        # Interception Stats
        'interceptions': {
            'category': 'defensiveInterceptions',
            'display_name': 'Interceptions',
            'abbreviation': 'INT',
            'description': 'Total interceptions',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['interceptions', 'ints', 'int', 'picks']
        },
        'interceptionTouchdowns': {
            'category': 'defensiveInterceptions',
            'display_name': 'Interception TDs',
            'abbreviation': 'TD',
            'description': 'Interceptions returned for touchdowns',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['interception touchdowns', 'int tds', 'pick sixes', 'pick six']
        },
        'interceptionYards': {
            'category': 'defensiveInterceptions',
            'display_name': 'Interception Yards',
            'abbreviation': 'INTYDS',
            'description': 'Yards gained on interception returns',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['interception yards', 'int yards', 'pick yards']
        },
        
        # Scoring Stats
        'passingTouchdowns': {
            'category': 'scoring',
            'display_name': 'Passing TDs',
            'abbreviation': 'PASS',
            'description': 'Passing touchdowns',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['passing touchdowns', 'passing tds', 'pass tds', 'td passes']
        },
        'receivingTouchdowns': {
            'category': 'scoring',
            'display_name': 'Receiving TDs',
            'abbreviation': 'REC',
            'description': 'Receiving touchdowns',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['receiving touchdowns', 'receiving tds', 'rec tds', 'td receptions']
        },
        'rushingTouchdowns': {
            'category': 'scoring',
            'display_name': 'Rushing TDs',
            'abbreviation': 'RUSH',
            'description': 'Rushing touchdowns',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['rushing touchdowns', 'rushing tds', 'rush tds', 'td runs']
        },
        'totalTouchdowns': {
            'category': 'scoring',
            'display_name': 'Total TDs',
            'abbreviation': 'TD',
            'description': 'Total touchdowns scored',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['total touchdowns', 'total tds', 'touchdowns', 'tds']
        },
        'totalPoints': {
            'category': 'scoring',
            'display_name': 'Total Points',
            'abbreviation': 'PTS',
            'description': 'Total points scored',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['total points', 'points', 'pts']
        },
        'fieldGoals': {
            'category': 'scoring',
            'display_name': 'Field Goals',
            'abbreviation': 'FG',
            'description': 'Field goals made',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['field goals', 'fg', 'field goal']
        },
        'kickExtraPoints': {
            'category': 'scoring',
            'display_name': 'Extra Points',
            'abbreviation': 'PAT',
            'description': 'Extra points made',
            'type': 'counting',
            'aggregatable': True,
            'user_terms': ['extra points', 'pat', 'xp', 'extra point']
        }
    }
    
    @classmethod
    def get_stat_info(cls, stat_name):
        """Get comprehensive information about a stat."""
        return cls.STATS_MAPPING.get(stat_name, {})
    
    @classmethod
    def find_stat_by_user_term(cls, user_term):
        """Find stat name by user's natural language term."""
        user_term_lower = user_term.lower().strip()
        
        for stat_name, info in cls.STATS_MAPPING.items():
            # Check direct name match
            if user_term_lower == stat_name.lower():
                return stat_name
                
            # Check user terms
            if user_term_lower in info.get('user_terms', []):
                return stat_name
                
            # Check display name
            if user_term_lower == info.get('display_name', '').lower():
                return stat_name
                
            # Check abbreviation
            if user_term_lower == info.get('abbreviation', '').lower():
                return stat_name
        
        return None
    
    @classmethod
    def get_aggregatable_stats(cls):
        """Get list of stats that can be aggregated across seasons/games."""
        return [name for name, info in cls.STATS_MAPPING.items() 
                if info.get('aggregatable', False)]
    
    @classmethod
    def get_stats_by_category(cls, category):
        """Get all stats in a specific category."""
        return [name for name, info in cls.STATS_MAPPING.items() 
                if info.get('category') == category]
    
    @classmethod
    def get_all_user_terms(cls):
        """Get all possible user terms for debugging/reference."""
        all_terms = []
        for stat_name, info in cls.STATS_MAPPING.items():
            all_terms.extend(info.get('user_terms', []))
            all_terms.append(stat_name.lower())
            if info.get('display_name'):
                all_terms.append(info.get('display_name').lower())
            if info.get('abbreviation'):
                all_terms.append(info.get('abbreviation').lower())
        return sorted(set(all_terms))