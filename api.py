import requests
import pandas as pd

API_KEY = "3c85e06129d2a1143eccdc0840f5bb4a"

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

params = {
    "league": 15,
    "season": 2025
}

url = "https://v3.football.api-sports.io/standings"
response = requests.get(url, headers=headers, params=params)
data = response.json()

if data["results"] > 0 and data["response"]:
    # Extract top 2 teams per group
    group_standings = data["response"][0]["league"]["standings"]

    top_teams = []
    for group in group_standings:
        for team_info in sorted(group, key=lambda x: x["rank"])[:2]:
            top_teams.append({
                "group": team_info["group"],
                "rank": team_info["rank"],
                "team": team_info["team"]["name"],
                "points": team_info["points"],
                "goal_diff": team_info["goalsDiff"]
            })

    df = pd.DataFrame(top_teams)
    print(df)
else:
    print("No standings data available for the selected league and season.")
    if "errors" in data and data["errors"]:
        print("API Errors:", data["errors"])