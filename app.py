from flask import Flask, jsonify, send_from_directory, render_template, url_for
import csv
import json
import os
from scrape_scores import scrape_with_requests

# --- Constants ---
BETS_FILE = 'bets.csv'
RESULTS_FILE = 'results.json'
FOTMOB_URL = "https://www.fotmob.com/leagues/78/table/fifa-club-world-cup"
POINTS = {
    "1/8": 2, "1/4": 4, "1/2": 8, "Final": 16, "Winner": 32, "BestStriker": 20
}

# --- Flask App Initialization ---
app = Flask(__name__)


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

    # Get all live games and their leaders
    matches = scrape_with_requests()
    live_leaders = set()
    live_teams = set()
    for m in matches:
        if m["status"] == "live":
            live_teams.add(m["team1"])
            live_teams.add(m["team2"])
            if m["winner"] and m["winner"] != "Draw":
                live_leaders.add(m["winner"])

    # Validate team-based rounds
    for round_key in ["1/8", "1/4", "1/2", "Final"]:
        teams = player_bet.get(round_key, "").split(';')
        result_set = results_sets.get(round_key)
        if teams and teams[0]:
            formatted_bets[round_key] = []
            for team in teams:
                status = "pending"
                if round_key == "1/4":
                    # Check if the team is in 1/4 or 1/4_losers
                    if team in results_data.get("1/4", []):
                        # Is the match still live?
                        is_live = False
                        for m in matches:
                            if (team == m["team1"] or team == m["team2"]) and m["status"] == "live" and m["winner"] == team:
                                is_live = True
                                break
                        status = "live-correct" if is_live else "correct"
                    elif team in results_data.get("1/4_losers", []):
                        # Is the match still live?
                        is_live = False
                        for m in matches:
                            if (team == m["team1"] or team == m["team2"]) and m["status"] == "live" and m["winner"] != team:
                                is_live = True
                                break
                        status = "live-wrong" if is_live else "incorrect"
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
    """Scrapes live data from scrape_scores, updates only '1/4' in results.json, and returns status."""
    print("Attempting to refresh live data...")
    try:
        matches = scrape_with_requests()
        if not matches:
            print("Scraping failed, no matches returned.")
            return jsonify({"success": False, "message": "Scraping failed to return any data."}), 500

        winners_1_4 = []
        losers_1_4 = []
        for m in matches:
            if m["status"] in ("finished", "live") and m["winner"] and m["winner"] != "Draw":
                winners_1_4.append(m["winner"])
                # Find the loser
                loser = m["team1"] if m["winner"] == m["team2"] else m["team2"]
                losers_1_4.append(loser)

        # Load current results.json to preserve '1/8' and other fields
        if os.path.exists(RESULTS_FILE):
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                results = json.load(f)
        else:
            results = {"1/8": [], "1/4": [], "1/4_losers": [], "1/2": [], "Final": [], "Winner": "", "BestStriker": ""}

        results["1/4"] = sorted(set(winners_1_4))
        results["1/4_losers"] = sorted(set(losers_1_4))

        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        print("Successfully updated '1/4' in results.json.")
        print(f"[DEBUG] Winners/leading teams for 1/4: {winners_1_4}")
        return jsonify({"success": True, "message": "Live data refreshed successfully!"})

    except Exception as e:
        print(f"An error occurred during the refresh process: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/live')
def get_live_game():
    """Returns the current live game and score, or None if no game is live."""
    matches = scrape_with_requests()
    live_matches = [m for m in matches if m["status"] == "live"]
    if live_matches:
        return jsonify(live_matches[0])
    return jsonify(None)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 