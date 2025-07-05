import requests
from bs4 import BeautifulSoup
import json

def scrape_final():
    url = "https://www.worldfootball.net/schedule/klub-wm-2025-finale/0/"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    matches = []
    table = soup.find("table", class_="standard_tabelle")
    if not table:
        return matches

    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 5:
            continue
        # Example columns: date, time, home, away, result
        team1 = cols[2].get_text(strip=True)
        team2 = cols[4].get_text(strip=True)
        score = cols[5].get_text(strip=True) if len(cols) > 5 else ""
        status = "upcoming"
        winner = None
        if score and (":" in score or "-" in score):
            # Score format: '2:1' or '1-0'
            score_clean = score.replace("-", ":")
            parts = score_clean.split(":")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                s1, s2 = int(parts[0]), int(parts[1])
                if s1 > s2:
                    winner = team1
                elif s2 > s1:
                    winner = team2
                else:
                    winner = "Draw"
                status = "finished"
            else:
                status = "live"
        match = {
            "team1": team1,
            "team2": team2,
            "score": score,
            "status": status,
            "winner": winner
        }
        matches.append(match)
    return matches

if __name__ == "__main__":
    matches = scrape_final()
    print("\n📊 Final Match Summary:")
    for m in matches:
        print(f"[{m['status'].upper()}] {m['team1']} {m['score']} {m['team2']} — Winner: {m['winner']}")
    # Optionally, save to a file
    with open("final.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2, ensure_ascii=False) 