import requests
from bs4 import BeautifulSoup
import time

def scrape_with_requests(url):
    """Scrape team data using requests instead of Selenium for Docker compatibility"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find all team names in the standings table
        team_elements = soup.select('span[data-testid^="standings-table-team-name-"] a')
        teams = [team.get_text(strip=True) for team in team_elements if team.get_text(strip=True)]
        
        return teams
        
    except Exception as e:
        print(f"Error scraping with requests: {e}")
        return []

if __name__ == '__main__':
    url = "https://www.fotmob.com/leagues/78/table/fifa-club-world-cup"
    print(scrape_with_requests(url))