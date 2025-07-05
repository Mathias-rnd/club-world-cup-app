import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

url = "https://www.worldfootball.net/goalgetter/klub-wm-2025/"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

rows = soup.select("table.standard_tabelle tr")[1:]
data = []

for row in rows:
    cols = row.find_all("td")
    if len(cols) < 6:
        continue

    try:
        rank = cols[0].get_text(strip=True).replace(".", "")
        player = cols[1].get_text(strip=True)

        # Country and flag
        country = cols[3].text.strip()
        country_flag_img = cols[2].find("img")
        country_flag_url = country_flag_img["src"] if country_flag_img else None

        # Club name and logo
        club_links = cols[4].find_all("a")
        club_name = club_links[-1].text.strip()
        club_logo_img = None
        for link in club_links:
            img = link.find("img")
            if img:
                club_logo_img = img["src"]
        club_logo_url = club_logo_img if club_logo_img else None

        # Goals and penalty
        goals_text = cols[5].get_text()
        goals = cols[5].find("b").text.strip()
        penalty = goals_text.split("(")[-1].split(")")[0] if "(" in goals_text else "0"

        data.append({
            "Rank": rank,
            "Player": player,
            "Country": country,
            "CountryFlagURL": country_flag_url,
            "Team": club_name,
            "TeamLogoURL": club_logo_url,
            "Goals": goals,
            "Penalties": penalty
        })

        if len(data) >= 10:
            break

    except Exception as e:
        print("Error parsing row:", e)

# After building your data list, before saving:
for idx, entry in enumerate(data):
    entry["Rank"] = str(idx + 1)  # Overwrite with 1-10

# Save or print
df = pd.DataFrame(data)
print(df)
# Optional: df.to_csv("top_scorers.csv", index=False)

with open("top_scorers.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)




# Name,1/8,1/4,1/2,Final,Winner,BestStriker
# Mathias,FC Porto;Inter Miami CF;Paris Saint-Germain;Atletico Madrid;Bayern 
# München;SL Benfica;Chelsea FC;Los Angeles FC;Inter;River Plate;Borussia 
# Dortmund;Fluminense RJ;Manchester City;Juventus;Real Madrid;Salzburg,River 
# Plate;Manchester City;Atletico Madrid;Bayern München;Paris Saint-Germain;SL 
# Benfica;Real Madrid;Inter,Manchester City;Bayern München;Paris Saint-Germain;
# Real Madrid,Paris Saint-Germain;Bayern München,Paris Saint-Germain,Kylian Mbappé
# Stéphane,FC Porto;Palmeiras;Paris Saint-Germain;Atletico Madrid;Bayern München;
# Boca Juniors;Chelsea FC;Flamengo RJ;Inter;River Plate;Borussia Dortmund;
# Fluminense RJ;Manchester City;Juventus;Real Madrid;Salzburg,Inter;Manchester 
# City;Atletico Madrid;Bayern München;Paris Saint-Germain;Boca Juniors;Real 
# Madrid;Borussia Dortmund,Manchester City;Bayern München;Paris Saint-Germain;
# Real Madrid,Bayern München;Real Madrid,Real Madrid,Kylian Mbappé
# Arthur,FC Porto;Palmeiras;Paris Saint-Germain;Botafogo - RJ;Bayern München;SL 
# Benfica;Chelsea FC;Flamengo RJ;Inter;River Plate;Borussia Dortmund;Fluminense 
# RJ;Manchester City;Juventus;Real Madrid;Al Hilal,Paris Saint-Germain;Real 
# Madrid;Manchester City;Fluminense RJ;Flamengo RJ;Bayern München;Palmeiras;
# Borussia Dortmund,Paris Saint-Germain;Bayern München;Manchester City;Real 
# Madrid,Paris Saint-Germain;Bayern München,Paris Saint-Germain,Michael Olise
# Yovan,FC Porto;Inter Miami CF;Paris Saint-Germain;Atletico Madrid;Bayern 
# München;Boca Juniors;Chelsea FC;Flamengo RJ;Inter;River Plate;Borussia Dortmund;
# Fluminense RJ;Manchester City;Juventus;Real Madrid;Al Hilal,Inter;Manchester 
# City;Real Madrid;Atletico Madrid;Bayern München;Paris Saint-Germain;Boca 
# Juniors;Borussia Dortmund,Real Madrid;Manchester City;Paris Saint-Germain;
# Bayern München,Bayern München;Paris Saint-Germain,Paris Saint-Germain,Khvicha 
# Kvaratskhelia