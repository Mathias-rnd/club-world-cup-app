import requests
from bs4 import BeautifulSoup
import json

def scrape_with_requests(url):
    """
    Scrapes the FotMob page for team names using the requests library.
    Returns a list of team names.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx or 5xx)

        soup = BeautifulSoup(response.content, 'lxml')
        
        # This selector needs to be very specific to FotMob's structure
        # Looking for a link inside a span with a specific data-testid
        team_links = soup.select('span[data-testid^="standings-table-team-name-"] a')
        
        team_names = [link.get_text(strip=True) for link in team_links]
        
        if not team_names:
            print("Warning: No team names were scraped. The website structure might have changed.")

        return team_names

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the web request: {e}")
        return []

if __name__ == '__main__':
    # For direct testing of this script
    fotmob_url = "https://www.fotmob.com/leagues/78/table/fifa-club-world-cup"
    scraped_teams = scrape_with_requests(fotmob_url)
    if scraped_teams:
        print("Successfully scraped the following teams:")
        print(json.dumps(scraped_teams, indent=2))
    else:
        print("Failed to scrape team names.")