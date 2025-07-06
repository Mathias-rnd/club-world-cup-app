import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}
TARGET_TEAMS = [
    "FC Porto",
    "Atlético Madrid",
    "Red Bull Salzburg",
    "Boca Juniors",
    "Los Angeles FC"
]

def find_team_id(team_name):
    # Search in soccer dropdown for leagues
    leagues = requests.get(
        "https://site.api.espn.com/apis/site/v2/leagues/dropdown",
        params={"sport": "soccer", "limit": 500},
        headers=HEADERS
    ).json().get("items", [])
    
    for league in leagues:
        slug = league.get("slug")
        resp = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/teams",
            headers=HEADERS
        )
        if not resp.ok:
            continue
        teams = resp.json().get("sports", [{}])[0]\
                      .get("leagues", [{}])[0]\
                      .get("teams", [])
        for entry in teams:
            name = entry["team"]["displayName"]
            if name.lower() == team_name.lower():
                return entry["team"]["id"], slug
    return None, None

results = {}
for t in TARGET_TEAMS:
    tid, league = find_team_id(t)
    if tid:
        results[t] = {"id": tid, "league": league}
    else:
        results[t] = None

print(results)
