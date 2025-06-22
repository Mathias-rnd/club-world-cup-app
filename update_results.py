import json
import os
from scrape import scrape_with_browser

# --- Configuration ---
# The URL to the FotMob standings page
FOTMOB_URL = "https://www.fotmob.com/leagues/78/table/fifa-club-world-cup"

# --- File Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(BASE_DIR, 'results.json')

def update_results_from_live_scrape():
    """
    Updates the results.json file by scraping live data from the web.
    """
    print("Starting live scrape from FotMob...")
    scraped_data = scrape_with_browser(FOTMOB_URL)

    if not scraped_data:
        print("Scraping failed. No data was returned. Aborting update.")
        return

    # Flatten the dictionary of teams into a single list of 16
    advancing_teams = []
    for group_name in sorted(scraped_data.keys()):
        advancing_teams.extend(scraped_data[group_name])

    if len(advancing_teams) != 16:
        print(f"Warning: Scraper found {len(advancing_teams)} teams, but expected 16.")
    
    print("Updating results.json with the live scraped teams...")
    
    # Load the existing results.json
    try:
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            results_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is empty, create a default structure
        results_data = {
            "1/8": [], "1/4": [], "1/2": [], "Final": [], "Winner": "", "BestStriker": ""
        }

    # Update the 1/8th final teams
    results_data["1/8"] = advancing_teams

    # Write the updated data back to the file
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)
        
    print("Successfully updated results.json with live data!")
    print(f"The 16 advancing teams are: {', '.join(advancing_teams)}")

# --- Main execution part ---
if __name__ == "__main__":
    update_results_from_live_scrape() 