import requests
from bs4 import BeautifulSoup

URL = "https://www.worldfootball.net/schedule/klub-wm-2025-achtelfinale/0/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean(cell):
    for img in cell.find_all("img"):
        img.decompose()
    return cell.get_text(strip=True)

def fetch_matches():
    r = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(r.content, "html.parser")

    table = soup.find("table", class_="standard_tabelle")
    if not table:
        print("❌ Match table not found.")
        return []

    matches = []

    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        date = clean(cols[0])
        time = clean(cols[1])
        team1 = clean(cols[2])
        team2 = clean(cols[4])
        score = clean(cols[5])

        # Skip incomplete rows
        if not team1 or not team2 or team2 == "-":
            continue

        match = {
            "date": date,
            "time": time,
            "team1": team1,
            "team2": team2,
            "status": "upcoming",
            "score": None,
            "winner": None
        }

        if score == "-":
            pass  # upcoming match
        elif "(" in score and ":" in score:
            match["status"] = "finished"
            score_clean = score.split()[0].strip("()")
            goals1, goals2 = map(int, score_clean.split(":"))
            match["score"] = f"{goals1}:{goals2}"
            if goals1 > goals2:
                match["winner"] = team1
            elif goals2 > goals1:
                match["winner"] = team2
            else:
                match["winner"] = "Draw"
        elif ":" in score:
            try:
                goals1, goals2 = map(int, score.split(":"))
                match["score"] = f"{goals1}:{goals2}"
                match["status"] = "live"
                if goals1 > goals2:
                    match["winner"] = team1
                elif goals2 > goals1:
                    match["winner"] = team2
                else:
                    match["winner"] = "Draw"
            except:
                match["status"] = "live"
                match["score"] = score

        matches.append(match)

    return matches

def display(matches):
    print("\n📊 Match Summary:")
    for m in matches:
        if m["status"] == "finished":
            print(f"[FINAL] {m['team1']} {m['score']} {m['team2']} — Winner: {m['winner']}")
        elif m["status"] == "live":
            print(f"[LIVE]  {m['team1']} {m['score']} {m['team2']} — Leading: {m['winner']}")
        else:
            print(f"[UPCOMING] {m['date']} {m['time']}: {m['team1']} vs {m['team2']}")

if __name__ == "__main__":
    matches = fetch_matches()
    display(matches)
    
def scrape_with_requests(*args, **kwargs):
    matches = fetch_matches()
    print(f"[DEBUG] scrape_with_requests fetched {len(matches)} matches.")
    for m in matches:
        print(f"[DEBUG] {m['status'].upper()}: {m['team1']} vs {m['team2']} | Winner: {m['winner']}")
    return matches



# Name,1/8,1/4,1/2,Final,Winner,BestStriker
# Mathias,FC Porto;Inter Miami CF;Paris Saint-Germain;Atletico Madrid;Bayern München;Benfica;Chelsea;Los Angeles FC;Inter;River Plate;Borussia Dortmund;Fluminense;Manchester City;Juventus;Real Madrid;Salzburg,River Plate;Manchester City;Atletico Madrid;Bayern München;Paris Saint-Germain;Benfica;Real Madrid;Inter,Manchester City;Bayern München;Paris Saint-Germain;Real Madrid,Paris Saint-Germain;Bayern München,Paris Saint-Germain,Kylian Mbappé
# Stephane,FC Porto;Palmeiras;Paris Saint-Germain;Atletico Madrid;Bayern München;Boca Juniors;Chelsea;Flamengo;Inter;River Plate;Borussia Dortmund;Fluminense;Manchester City;Juventus;Real Madrid;Salzburg,Inter;Manchester City;Atletico Madrid;Bayern München;Paris Saint-Germain;Boca Juniors;Real Madrid;Borussia Dortmund,Manchester City;Bayern München;Paris Saint-Germain;Real Madrid,Bayern München;Real Madrid,Real Madrid,Kylian Mbappé
# Arthur,FC Porto;Palmeiras;Paris Saint-Germain;Botafogo RJ;Bayern München;Benfica;Chelsea;Flamengo;Inter;River Plate;Borussia Dortmund;Fluminense;Manchester City;Juventus;Real Madrid;Al Hilal,Paris Saint-Germain;Real Madrid;Manchester City;Fluminense;Flamengo;Bayern München;Palmeiras;Borussia Dortmund,Paris Saint-Germain;Bayern München;Manchester City;Real Madrid,Paris Saint-Germain;Bayern München,Paris Saint-Germain,Michael Olise
# Yovan,FC Porto;Inter Miami CF;Paris Saint-Germain;Atletico Madrid;Bayern München;Boca Juniors;Chelsea;Flamengo;Inter;River Plate;Borussia Dortmund;Fluminense;Manchester City;Juventus;Real Madrid;Al Hilal,Inter;Manchester City;Real Madrid;Atletico Madrid;Bayern München;Paris Saint-Germain;Boca Juniors;Borussia Dortmund,Real Madrid;Manchester City;Paris Saint-Germain;Bayern München,Bayern München;Paris Saint-Germain,Paris Saint-Germain,Khvicha Kvaratskhelia