"""
CDMC (Coupe du Monde des Clubs) Prediction Web App
==================================================

A Flask web application for managing Club World Cup predictions, including:
- Leaderboard with live scoring
- Joker prediction system for bonus points
- Live match updates
- Top scorers tracking
- Admin dashboard for managing predictions

Main application file that handles all routes and business logic.
"""

from flask import Flask, jsonify, send_from_directory, render_template, url_for, request, session, redirect
import csv
import json
import os
from scrape_round_of_16 import scrape_with_requests as scrape_round_of_16_with_requests
import subprocess
from functools import wraps
from scrape_quarter_finals import scrape_with_requests as scrape_quarter_finals_with_requests
from scrape_semi_finals import scrape_with_requests as scrape_semi_finals_with_requests
import importlib.util

# --- Constants ---
BETS_FILE = 'bets.csv'
RESULTS_FILE = 'results.json'
FOTMOB_URL = "https://www.fotmob.com/leagues/78/table/fifa-club-world-cup"
POINTS = {
    "1/8": 2, "1/4": 4, "1/2": 8, "Final": 16, "Winner": 32, "BestStriker": 20
}
ADMIN_PASSWORD = "ale6969"  # Change this to your preferred password

# --- Flask App Initialization ---
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this in production

# --- Admin Authentication ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_joker_format(joker_text):
    """Validate joker prediction format: 'Team1 vs Team2: Score1-Score2'"""
    if not joker_text or not joker_text.strip():
        return True, ""  # Empty is valid
    
    try:
        # Check for the required format
        if ':' not in joker_text or 'vs' not in joker_text:
            return False, "Format must be: 'Team1 vs Team2: Score1-Score2'"
        
        parts = joker_text.split(':')
        if len(parts) != 2:
            return False, "Format must be: 'Team1 vs Team2: Score1-Score2'"
        
        match_part = parts[0].strip()
        score_part = parts[1].strip()
        
        # Check teams part
        teams = match_part.split('vs')
        if len(teams) != 2:
            return False, "Format must be: 'Team1 vs Team2: Score1-Score2'"
        
        team1 = teams[0].strip()
        team2 = teams[1].strip()
        
        if not team1 or not team2:
            return False, "Both team names are required"
        
        # Check score part
        score_parts = score_part.split('-')
        if len(score_parts) != 2:
            return False, "Score format must be: 'Score1-Score2'"
        
        score1 = int(score_parts[0])
        score2 = int(score_parts[1])
        
        if score1 < 0 or score2 < 0:
            return False, "Scores must be non-negative numbers"
        
        return True, ""
        
    except ValueError:
        return False, "Scores must be valid numbers"
    except Exception as e:
        return False, f"Invalid format: {str(e)}"

def save_bets_to_csv(bets_data):
    """Save bets data back to CSV file"""
    try:
        with open(BETS_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Name', '1/8', '1/4', '1/2', 'Final', 'Winner', 'BestStriker', 
                         'Joker_1_8_1', 'Joker_1_8_2', 'Joker_1_8_3', 
                         'Joker_1_4_1', 'Joker_1_4_2', 'Joker_1_2_1']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for bet in bets_data:
                writer.writerow(bet)
        return True, "Bets updated successfully"
    except Exception as e:
        return False, f"Error saving bets: {str(e)}"

# --- Helper Functions (for calculating scores) ---
def load_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.json'):
                return json.load(f)
            else:
                return list(csv.DictReader(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def compute_score(bet, results):
    score = 0
    for round_name in ["1/8", "1/4", "1/2", "Final"]:
        actual_teams = {str(team).strip().lower() for team in results.get(round_name, [])}
        bet_teams_str = bet.get(round_name, "")
        bet_teams = {team.strip().lower() for team in bet_teams_str.split(';')} if bet_teams_str else set()
        
        # For 1/4 and 1/2, also check if teams actually played in those rounds
        if round_name == "1/4":
            all_1_4_teams = {str(team).strip().lower() for team in results.get("1/4", []) + results.get("1/4_losers", [])}
            # Only count teams that actually played in 1/4 finals
            bet_teams = bet_teams & all_1_4_teams
        elif round_name == "1/2":
            all_1_2_teams = {str(team).strip().lower() for team in results.get("1/2", []) + results.get("1/2_losers", [])}
            # Only count teams that actually played in 1/2 finals
            bet_teams = bet_teams & all_1_2_teams
        
        score += len(bet_teams & actual_teams) * POINTS.get(round_name, 0)
    
    if bet.get("Winner", "").strip().lower() == results.get("Winner", "").strip().lower():
        score += POINTS["Winner"]
    if bet.get("BestStriker", "").strip().lower() == results.get("BestStriker", "").strip().lower():
        score += POINTS["BestStriker"]
    
    # Add joker points for all rounds
    joker_points = 0
    
    # Round of 16 jokers (3 jokers)
    for i in range(1, 4):
        joker_key = f"Joker_1_8_{i}"
        if joker_key in bet:
            joker_points += compute_joker_points(bet.get(joker_key, ""), results)
    
    # Quarter finals jokers (2 jokers)
    for i in range(1, 3):
        joker_key = f"Joker_1_4_{i}"
        if joker_key in bet:
            joker_points += compute_joker_points(bet.get(joker_key, ""), results)
    
    # Semi-finals jokers (1 joker)
    joker_key = "Joker_1_2_1"
    if joker_key in bet:
        joker_points += compute_joker_points(bet.get(joker_key, ""), results)
    
    score += joker_points
    
    return score

def team_names_match(team1, team2):
    """Check if two team names match, handling common variations and typos."""
    t1 = team1.lower().strip()
    t2 = team2.lower().strip()
    
    # Exact match
    if t1 == t2:
        return True
    
    # Common variations
    variations = {
        'palmeiras': ['palmeira'],
        'chelsea fc': ['chelsea'],
        'manchester city': ['man city'],
        'real madrid': ['madrid'],
        'bayern münchen': ['bayern munchen', 'bayern'],
        'paris saint-germain': ['psg', 'paris sg'],
        'inter': ['inter milan'],
        'juventus': ['juve'],
        'borussia dortmund': ['dortmund'],
        'sl benfica': ['benfica'],
        'flamengo rj': ['flamengo'],
        'fluminense rj': ['fluminense'],
        'botafogo - rj': ['botafogo rj', 'botafogo'],
        'cf monterrey': ['monterrey'],
        'al hilal': ['hilal'],
        'boca juniors': ['boca'],
        'inter miami cf': ['inter miami'],
        'los angeles fc': ['la fc', 'la galaxy'],
        'river plate': ['river'],
        'salzburg': ['rb salzburg', 'red bull salzburg'],
        'atletico madrid': ['atletico', 'atletico de madrid']
    }
    
    # Check if either team is in the variations
    for main_name, variants in variations.items():
        if t1 == main_name and t2 in variants:
            return True
        if t2 == main_name and t1 in variants:
            return True
        if t1 in variants and t2 in variants:
            return True
    
    return False

def compute_joker_points(joker_prediction, results):
    """Calculate joker points based on prediction vs actual result."""
    if not joker_prediction or not joker_prediction.strip():
        return 0
    
    try:
        # Parse joker prediction: "Team1 vs Team2: Score1-Score2"
        parts = joker_prediction.split(":")
        if len(parts) != 2:
            return 0
        
        match_part = parts[0].strip()
        score_part = parts[1].strip()
        
        # Parse teams
        teams = match_part.split("vs")
        if len(teams) != 2:
            return 0
        
        predicted_team1 = teams[0].strip()
        predicted_team2 = teams[1].strip()
        
        # Parse predicted score
        score_parts = score_part.split("-")
        if len(score_parts) != 2:
            return 0
        
        predicted_score1 = int(score_parts[0])
        predicted_score2 = int(score_parts[1])
        predicted_winner = predicted_team1 if predicted_score1 > predicted_score2 else predicted_team2
        
        # Get actual results from the correct scraper based on the teams involved
        # For now, we'll check both scrapers since we don't know which round the match belongs to
        matches_1_8 = scrape_round_of_16_with_requests()
        matches_1_4 = scrape_quarter_finals_with_requests()
        matches_1_2 = scrape_semi_finals_with_requests()
        all_matches = matches_1_8 + matches_1_4 + matches_1_2
        
        for match in all_matches:
            # Check if this match involves the predicted teams
            if ((team_names_match(match["team1"], predicted_team1) and team_names_match(match["team2"], predicted_team2)) or
                (team_names_match(match["team1"], predicted_team2) and team_names_match(match["team2"], predicted_team1))):
                
                if match["status"] == "finished" and match["score"]:
                    # Parse actual score
                    actual_score_parts = match["score"].split(":")
                    if len(actual_score_parts) == 2:
                        actual_score1 = int(actual_score_parts[0])
                        actual_score2 = int(actual_score_parts[1])
                        actual_winner = match["team1"] if actual_score1 > actual_score2 else match["team2"]
                        
                        # Calculate points
                        if predicted_score1 == actual_score1 and predicted_score2 == actual_score2:
                            return 4  # Exact score prediction
                        elif team_names_match(predicted_winner, actual_winner):
                            return 2  # Correct winner
                        else:
                            return -3  # Wrong winner
                elif match["status"] == "live":
                    # Match is live, return 0 (pending)
                    return 0
                
                break
        
        return 0  # Match not found or not finished
        
    except (ValueError, IndexError) as e:
        print(f"Error parsing joker prediction '{joker_prediction}': {e}")
        return 0

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'cdmc_logo.ico')

# --- Routes ---
@app.route('/')
def index():
    """Serves the main leaderboard HTML file."""
    return render_template('leaderboard.html')

@app.route('/api/leaderboard')
def get_leaderboard():
    """Returns the current leaderboard based on the last known results."""
    bets = load_data(BETS_FILE)
    results = load_data(RESULTS_FILE)
    leaderboard = [{'name': bet['Name'], 'score': compute_score(bet, results)} for bet in bets]
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(leaderboard)

@app.route('/api/bets/<player_name>')
def get_player_bets(player_name):
    """Returns the detailed bets for a specific player, with correctness validation."""
    bets_data = load_data(BETS_FILE)
    results_data = load_data(RESULTS_FILE)
    player_bet = next((bet for bet in bets_data if bet['Name'] == player_name), None)

    if not player_bet:
        return jsonify({"success": False, "message": "Player not found."}), 404

    def check_bet_status(bet, result_set):
        if not result_set:
            return "pending"
        return "correct" if bet in result_set else "incorrect"

    results_sets = {
        "1/8": set(results_data.get("1/8", [])),
        "1/4": set(results_data.get("1/4", [])),
        "1/2": set(results_data.get("1/2", [])),
        "Final": set(results_data.get("Final", [])),
    }

    formatted_bets = {}

    eliminated_teams = set()
    for round_key in ["1/8", "1/4", "1/2", "Final"]:
        teams = player_bet.get(round_key, "").split(';')
        result_set = results_sets.get(round_key)
        if teams and teams[0]:
            formatted_bets[round_key] = []
            for team in teams:
                status = "pending"
                if round_key == "1/4":
                    all_1_4_teams = set(results_data.get("1/4", []) + results_data.get("1/4_losers", []))
                    if team in results_data.get("1/4", []):
                        status = "correct"
                    elif team in results_data.get("1/4_losers", []):
                        status = "incorrect"
                        eliminated_teams.add(team)
                    elif team not in all_1_4_teams:
                        status = "incorrect"
                        eliminated_teams.add(team)
                    else:
                        status = "pending"
                elif round_key == "1/2":
                    all_1_2_teams = set(results_data.get("1/2", []) + results_data.get("1/2_losers", []))
                    if team in results_data.get("1/2", []):
                        status = "correct"
                    elif team in results_data.get("1/2_losers", []):
                        status = "incorrect"
                        eliminated_teams.add(team)
                    elif team not in all_1_2_teams:
                        status = "incorrect"
                        eliminated_teams.add(team)
                    else:
                        status = "pending"
                elif round_key == "Final":
                    if team in eliminated_teams:
                        status = "incorrect"
                    else:
                        # If the final hasn't been played yet, mark as pending
                        final_teams = results_data.get("Final", [])
                        winner = results_data.get("Winner", "")
                        # Check for placeholders or empty final
                        final_not_played = not winner or any(t in ["N.N.", "", None] for t in final_teams)
                        if final_not_played:
                            status = "pending"
                        else:
                            if team in final_teams:
                                status = "correct"
                            else:
                                status = "incorrect"
                else:
                    status = check_bet_status(team, result_set)
                formatted_bets[round_key].append({"team": team, "status": status})
        else:
            formatted_bets[round_key] = []

    # Validate Winner
    winner_bet = player_bet.get("Winner", "")
    winner_result = results_data.get("Winner", "")
    if winner_bet:
        status = "pending"
        if winner_bet in eliminated_teams:
            status = "incorrect"
        elif winner_result:
            status = "correct" if winner_bet == winner_result else "incorrect"
        formatted_bets["Winner"] = {"team": winner_bet, "status": status}
    else:
        formatted_bets["Winner"] = None

    # Best Striker is always pending for now
    striker_bet = player_bet.get("BestStriker", "")
    striker_result = results_data.get("BestStriker", "")
    if striker_bet:
        status = "pending"
        if striker_result:
            status = "correct" if striker_bet == striker_result else "incorrect"
        formatted_bets["BestStriker"] = {"team": striker_bet, "status": status}
    else:
        formatted_bets["BestStriker"] = None

    # Joker predictions for all rounds
    formatted_bets["Jokers"] = {}
    jokers_1_8 = []
    for i in range(1, 4):
        joker_key = f"Joker_1_8_{i}"
        joker_bet = player_bet.get(joker_key, "")
        if joker_bet and joker_bet.strip():
            joker_points = compute_joker_points(joker_bet, results_data)
            if joker_points == 4:
                status = "correct"
            elif joker_points == 2:
                status = "partial"
            elif joker_points == -3:
                status = "incorrect"
            else:
                status = "pending"
            jokers_1_8.append({"team": joker_bet, "status": status, "points": joker_points})
        else:
            jokers_1_8.append(None)
    formatted_bets["Jokers"]["1/8"] = jokers_1_8
    jokers_1_4 = []
    for i in range(1, 3):
        joker_key = f"Joker_1_4_{i}"
        joker_bet = player_bet.get(joker_key, "")
        if joker_bet and joker_bet.strip():
            joker_points = compute_joker_points(joker_bet, results_data)
            if joker_points == 4:
                status = "correct"
            elif joker_points == 2:
                status = "partial"
            elif joker_points == -3:
                status = "incorrect"
            else:
                status = "pending"
            jokers_1_4.append({"team": joker_bet, "status": status, "points": joker_points})
        else:
            jokers_1_4.append(None)
    formatted_bets["Jokers"]["1/4"] = jokers_1_4
    joker_key = "Joker_1_2_1"
    joker_bet = player_bet.get(joker_key, "")
    if joker_bet and joker_bet.strip():
        joker_points = compute_joker_points(joker_bet, results_data)
        if joker_points == 4:
            status = "correct"
        elif joker_points == 2:
            status = "partial"
        elif joker_points == -3:
            status = "incorrect"
        else:
            status = "pending"
        formatted_bets["Jokers"]["1/2"] = [{"team": joker_bet, "status": status, "points": joker_points}]
    else:
        formatted_bets["Jokers"]["1/2"] = [None]

    return jsonify(formatted_bets)

@app.route('/api/refresh_quarters', methods=['POST'])
def refresh_quarters_data():
    """Scrapes semi-finals data, updates only '1/2' and '1/2_losers' in results.json, and returns status."""
    print("Attempting to refresh semi-finals data...")
    try:
        matches = scrape_semi_finals_with_requests()
        if not matches:
            print("Scraping failed, no matches returned.")
            return jsonify({"success": False, "message": "Scraping failed to return any data."}), 500

        winners_1_2 = []
        losers_1_2 = []
        for m in matches:
            if m["status"] in ("finished", "live") and m["winner"] and m["winner"] != "Draw":
                winners_1_2.append(m["winner"])
                # Find the loser
                loser = m["team1"] if m["winner"] == m["team2"] else m["team2"]
                losers_1_2.append(loser)

        # Load current results.json to preserve earlier rounds and other fields
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
        else:
            results = {"1/8": [], "1/4": [], "1/4_losers": [], "1/2": [], "1/2_losers": [], "Final": [], "Winner": "", "BestStriker": ""}

        results["1/2"] = sorted(set(winners_1_2))
        results["1/2_losers"] = sorted(set(losers_1_2))

        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        print("Successfully updated '1/2' and '1/2_losers' in results.json.")
        print(f"[DEBUG] Winners/leading teams for 1/2: {winners_1_2}")
        return jsonify({"success": True, "message": "Semi-finals data refreshed successfully!"})

    except Exception as e:
        print(f"An error occurred during the semi-finals refresh process: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/live')
def get_live_game():
    """Returns the current live or next game and score, from all rounds (1/8, 1/4, 1/2)."""
    matches_1_8 = scrape_round_of_16_with_requests()
    matches_1_4 = scrape_quarter_finals_with_requests()
    matches_1_2 = scrape_semi_finals_with_requests()
    all_matches = matches_1_8 + matches_1_4 + matches_1_2
    # Sort by date/time if possible, fallback to order
    live_matches = [m for m in all_matches if m["status"] == "live"]
    if live_matches:
        return jsonify(live_matches[0])
    # If no live, show next upcoming
    upcoming = [m for m in all_matches if m["status"] == "upcoming"]
    if upcoming:
        return jsonify(upcoming[0])
    return jsonify(None)

def scrape_final_with_requests():
    spec = importlib.util.spec_from_file_location("scrape_final", "scrape_final.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.scrape_final()

@app.route('/api/refresh_all', methods=['POST'])
def refresh_all_data():
    """Refreshes all rounds: 1/8, 1/4, 1/2, and final, updating results.json for all."""
    try:
        # Round of 16 scraper returns teams that qualified for Quarter Finals
        matches_1_8 = scrape_round_of_16_with_requests()
        winners_1_8 = []
        losers_1_8 = []
        teams_1_8 = set()
        for m in matches_1_8:
            if m["team1"]:
                teams_1_8.add(m["team1"])
            if m["team2"]:
                teams_1_8.add(m["team2"])
            if m["status"] in ("finished", "live") and m["winner"] and m["winner"] != "Draw":
                winners_1_8.append(m["winner"])
                loser = m["team1"] if m["winner"] == m["team2"] else m["team2"]
                losers_1_8.append(loser)
        
        # Quarter Finals scraper returns teams that qualified for Semi-Finals
        matches_1_4 = scrape_quarter_finals_with_requests()
        winners_1_4 = []
        losers_1_4 = []
        for m in matches_1_4:
            if m["status"] in ("finished", "live") and m["winner"] and m["winner"] != "Draw":
                winners_1_4.append(m["winner"])
                loser = m["team1"] if m["winner"] == m["team2"] else m["team2"]
                losers_1_4.append(loser)
        
        # Semi-Finals scraper returns teams that qualified for Final
        matches_1_2 = scrape_semi_finals_with_requests()
        winners_1_2 = []
        losers_1_2 = []
        for m in matches_1_2:
            if m["status"] in ("finished", "live") and m["winner"] and m["winner"] != "Draw":
                winners_1_2.append(m["winner"])
                loser = m["team1"] if m["winner"] == m["team2"] else m["team2"]
                losers_1_2.append(loser)
        
        # Final scraper
        matches_final = scrape_final_with_requests()
        final_teams = []
        final_winner = ""
        for m in matches_final:
            if m["team1"] and m["team2"]:
                final_teams = [m["team1"], m["team2"]]
            if m["status"] == "finished" and m["winner"] and m["winner"] != "Draw":
                final_winner = m["winner"]
        
        # Load and update results.json
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
        else:
            results = {"1/8": [], "1/8_losers": [], "1/4": [], "1/4_losers": [], "1/2": [], "1/2_losers": [], "Final": [], "Winner": "", "BestStriker": ""}
        
        # Set 1/8 to all unique teams that played in round of 16
        results["1/8"] = sorted(teams_1_8)
        
        # Round of 16 winners (teams qualified for Quarter Finals) → "1/4"
        results["1/4"] = sorted(set(winners_1_8))
        results["1/4_losers"] = sorted(set(losers_1_8))
        
        # Quarter Finals winners (teams qualified for Semi-Finals) → "1/2"
        results["1/2"] = sorted(set(winners_1_4))
        results["1/2_losers"] = sorted(set(losers_1_4))
        
        # Semi-Finals winners (teams qualified for Final) → "Final"
        results["Final"] = sorted(set(winners_1_2))
        
        # Final teams and winner
        if final_teams:
            results["Final"] = final_teams
        if final_winner:
            results["Winner"] = final_winner
        
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        
        return jsonify({"success": True, "message": "All rounds refreshed!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/top_scorers')
def get_top_scorers():
    try:
        if not os.path.exists("top_scorers.json"):
            print("top_scorers.json not found, returning empty list")
            return jsonify([])
        
        with open("top_scorers.json", "r", encoding="utf-8") as f:
            scorers = json.load(f)
        return jsonify(scorers)
    except FileNotFoundError:
        print("top_scorers.json file not found")
        return jsonify([])
    except json.JSONDecodeError as e:
        print(f"Error parsing top_scorers.json: {e}")
        return jsonify([])
    except Exception as e:
        print(f"Unexpected error reading top_scorers.json: {e}")
        return jsonify([])

@app.route('/api/refresh_top_scorers', methods=['POST'])
def refresh_top_scorers():
    try:
        print("Attempting to refresh top scorers...")
        
        # Check if scrape_top_scorers.py exists
        if not os.path.exists('scrape_top_scorers.py'):
            print("Error: scrape_top_scorers.py not found")
            return jsonify({"success": False, "message": "scrape_top_scorers.py not found"}), 500
        
        # Try to run the script
        result = subprocess.run(['python3', 'scrape_top_scorers.py'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        print("Top scorers refresh completed successfully")
        print(f"Output: {result.stdout}")
        
        # Verify the file was created/updated
        if os.path.exists('top_scorers.json'):
            print("top_scorers.json file exists and was updated")
            return jsonify({"success": True, "message": "Top scorers refreshed!"})
        else:
            print("Error: top_scorers.json was not created")
            return jsonify({"success": False, "message": "top_scorers.json was not created"}), 500
            
    except subprocess.CalledProcessError as e:
        print(f"Subprocess error: {e}")
        print(f"Return code: {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return jsonify({"success": False, "message": f"Script execution failed: {e.stderr}"}), 500
    except Exception as e:
        print(f"Unexpected error during top scorers refresh: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# --- Admin Routes ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid password")
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    bets = load_data(BETS_FILE)
    return render_template('admin_dashboard.html', bets=bets)

@app.route('/api/admin/update_joker', methods=['POST'])
@admin_required
def update_joker():
    try:
        data = request.get_json()
        player_name = data.get('player_name')
        joker_key = data.get('joker_key')  # e.g., 'Joker_1_8_1', 'Joker_1_4_2', etc.
        joker_prediction = data.get('joker_prediction', '').strip()
        
        if not player_name:
            return jsonify({"success": False, "message": "Player name is required"}), 400
        
        if not joker_key:
            return jsonify({"success": False, "message": "Joker key is required"}), 400
        
        # Validate joker key format
        valid_keys = ['Joker_1_8_1', 'Joker_1_8_2', 'Joker_1_8_3', 'Joker_1_4_1', 'Joker_1_4_2', 'Joker_1_2_1']
        if joker_key not in valid_keys:
            return jsonify({"success": False, "message": "Invalid joker key"}), 400
        
        # Validate joker format
        is_valid, error_message = validate_joker_format(joker_prediction)
        if not is_valid:
            return jsonify({"success": False, "message": error_message}), 400
        
        # Load current bets
        bets = load_data(BETS_FILE)
        
        # Find and update the player's joker
        player_found = False
        for bet in bets:
            if bet['Name'] == player_name:
                bet[joker_key] = joker_prediction
                player_found = True
                break
        
        if not player_found:
            return jsonify({"success": False, "message": "Player not found"}), 404
        
        # Save back to CSV
        success, message = save_bets_to_csv(bets)
        if not success:
            return jsonify({"success": False, "message": message}), 500
        
        return jsonify({"success": True, "message": f"Joker prediction updated for {player_name}"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error updating joker: {str(e)}"}), 500

@app.route('/api/admin/get_bets')
@admin_required
def get_bets_for_admin():
    try:
        bets = load_data(BETS_FILE)
        return jsonify({"success": True, "bets": bets})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error loading bets: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 