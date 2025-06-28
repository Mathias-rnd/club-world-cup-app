from flask import Flask, jsonify, send_from_directory
import csv
import json
import os
from scrape import scrape_with_requests

# --- Constants ---
BETS_FILE = 'bets.csv'
RESULTS_FILE = 'results.json'
FOTMOB_URL = "https://www.fotmob.com/leagues/78/table/fifa-club-world-cup"
POINTS = {
    "1/8": 2, "1/4": 4, "1/2": 8, "Final": 16, "Winner": 32, "BestStriker": 20
}

# --- Flask App Initialization ---
app = Flask(__name__)

# Test comment for automatic deployment - 2025-01-23

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
        score += len(bet_teams & actual_teams) * POINTS.get(round_name, 0)
    if bet.get("Winner", "").strip().lower() == results.get("Winner", "").strip().lower():
        score += POINTS["Winner"]
    if bet.get("BestStriker", "").strip().lower() == results.get("BestStriker", "").strip().lower():
        score += POINTS["BestStriker"]
    return score

# --- Routes ---
@app.route('/')
def index():
    """Serves the main leaderboard HTML file."""
    return send_from_directory('.', 'leaderboard.html')

@app.route('/script.js')
def script():
    """Serves the JavaScript file."""
    return send_from_directory('.', 'script.js')

@app.route('/favicon.svg')
def favicon():
    """Serves the favicon image."""
    return send_from_directory('.', 'favicon.svg')

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

    # Helper to check correctness of a bet against a set of results
    def check_bet_status(bet, result_set):
        if not result_set:
            return "pending"
        return "correct" if bet in result_set else "incorrect"

    # Pre-process results into sets for efficient lookup
    results_sets = {
        "1/8": set(results_data.get("1/8", [])),
        "1/4": set(results_data.get("1/4", [])),
        "1/2": set(results_data.get("1/2", [])),
        "Final": set(results_data.get("Final", [])),
    }

    formatted_bets = {}

    # Validate team-based rounds
    for round_key in ["1/8", "1/4", "1/2", "Final"]:
        teams = player_bet.get(round_key, "").split(';')
        result_set = results_sets.get(round_key)
        if teams and teams[0]:
            formatted_bets[round_key] = [
                {"team": team, "status": check_bet_status(team, result_set)} for team in teams
            ]
        else:
            formatted_bets[round_key] = []

    # Validate Winner
    winner_bet = player_bet.get("Winner", "")
    winner_result = results_data.get("Winner", "")
    if winner_bet:
        status = "pending"
        if winner_result:
            status = "correct" if winner_bet == winner_result else "incorrect"
        formatted_bets["Winner"] = {"team": winner_bet, "status": status}
    else:
        formatted_bets["Winner"] = None

    # Best Striker is always pending for now
    striker_bet = player_bet.get("BestStriker", "")
    if striker_bet:
        formatted_bets["BestStriker"] = {"team": striker_bet, "status": "pending"}
    else:
        formatted_bets["BestStriker"] = None

    return jsonify(formatted_bets)

@app.route('/api/refresh', methods=['POST'])
def refresh_live_data():
    """Scrapes live data from FotMob, updates results.json, and returns status."""
    print("Attempting to refresh live data...")
    try:
        # Use the new, lightweight scraper
        live_teams = scrape_with_requests(FOTMOB_URL)

        if not live_teams:
            print("Scraping failed, no teams returned.")
            return jsonify({"success": False, "message": "Scraping failed to return any data."}), 500

        # Since the new scraper returns a flat list, we need to decide how to map it.
        # For now, we'll assume the top 16 are the "1/8" finalists.
        # This logic might need adjustment based on FotMob's page layout.
        results = {"1/8": live_teams[:16]}

        with open(RESULTS_FILE, 'w') as f:
            json.dump(results, f, indent=4)

        print("Successfully updated results.json.")
        return jsonify({"success": True, "message": "Live data refreshed successfully!"})

    except Exception as e:
        print(f"An error occurred during the refresh process: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 