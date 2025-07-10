import requests
from bs4 import BeautifulSoup

URL = "https://www.worldfootball.net/schedule/klub-wm-2025-halbfinale/0/"
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
            "winner": None,
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
            except:  # noqa: E722
                match["status"] = "live"
                match["score"] = score

        matches.append(match)

    return matches


def display(matches):
    print("\n📊 Semi-Finals Match Summary:")
    for m in matches:
        if m["status"] == "finished":
            print(
                f"[FINAL] {m['team1']} {m['score']} {m['team2']} — Winner: {m['winner']}"
            )
        elif m["status"] == "live":
            print(
                f"[LIVE]  {m['team1']} {m['score']} {m['team2']} — Leading: {m['winner']}"
            )
        else:
            print(f"[UPCOMING] {m['date']} {m['time']}: {m['team1']} vs {m['team2']}")


if __name__ == "__main__":
    matches = fetch_matches()
    display(matches)


def scrape_with_requests(*args, **kwargs):
    matches = fetch_matches()
    print(f"[DEBUG] scrape_with_requests fetched {len(matches)} semi-finals matches.")
    for m in matches:
        print(
            f"[DEBUG] {m['status'].upper()}: {m['team1']} vs {m['team2']} | Winner: {m['winner']}"
        )
    return matches
