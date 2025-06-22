import csv
import json
import os

# Points per round
POINTS = {
    "1/8": 2,
    "1/4": 4,
    "1/2": 8,
    "Final": 16,
    "Winner": 32,
    "BestStriker": 20
}

# --- Robust File Paths ---
# This will find the files correctly, no matter where you run the script from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BETS_FILE = os.path.join(BASE_DIR, 'bets.csv')
RESULTS_FILE = os.path.join(BASE_DIR, 'results.json')

def load_bets(filename):
    bets = []
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bets.append(row)
    return bets

def load_results(filename):
    with open(filename) as f:
        return json.load(f)

def compute_score(bet, results):
    """Computes a score, ignoring case and extra whitespace."""
    score = 0
    for round_name in ["1/8", "1/4", "1/2", "Final"]:
        actual_teams = {team.strip().lower() for team in results.get(round_name, [])}
        bet_teams_str = bet.get(round_name, "")
        bet_teams = {team.strip().lower() for team in bet_teams_str.split(';')} if bet_teams_str else set()
        score += len(bet_teams & actual_teams) * POINTS[round_name]

    # Winner - case and space insensitive
    if bet.get("Winner", "").strip().lower() == results.get("Winner", "").strip().lower():
        score += POINTS["Winner"]

    # Best Striker - case and space insensitive
    if bet.get("BestStriker", "").strip().lower() == results.get("BestStriker", "").strip().lower():
        score += POINTS["BestStriker"]
        
    return score

def main():
    """Loads data, computes scores, and prints a sorted leaderboard."""
    bets = load_bets(BETS_FILE)
    results = load_results(RESULTS_FILE)
    
    leaderboard = []
    for bet in bets:
        score = compute_score(bet, results)
        leaderboard.append({'name': bet['Name'], 'score': score})
    
    # Sort by score descending
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    
    print("--- Leaderboard ---")
    for entry in leaderboard:
        print(f"{entry['name']}: {entry['score']} points")

if __name__ == "__main__":
    main() 