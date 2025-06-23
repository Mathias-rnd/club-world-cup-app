from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import json
import time

def scrape_round_of_16_matches(url: str):
    """
    Launches a browser, navigates directly to the filtered Round of 16 URL,
    handles cookies, waits for the matches to appear, and then scrapes them.

    Args:
        url (str): The specific URL for the Round of 16 matches.

    Returns:
        list: A list of dictionaries, where each dictionary represents a match-up.
    """
    all_matchups = []
    
    with sync_playwright() as p:
        try:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print(f"Navigating to the correct URL: {url}...")
            page.goto(url, wait_until='domcontentloaded', timeout=60000)

            # STEP 1: Handle Cookie Consent (this is still necessary)
            cookie_consent_button_selector = "button:has-text('Consent')"
            try:
                print("Looking for cookie consent button...")
                page.wait_for_selector(cookie_consent_button_selector, timeout=10000)
                print("Cookie consent button found. Clicking it...")
                page.click(cookie_consent_button_selector)
                # A brief pause to ensure the overlay is gone
                time.sleep(1) 
            except PlaywrightTimeoutError:
                print("Cookie consent button not found or already handled.")

            # STEP 2: Wait for the list of matches to be visible
            # We look for any match link to confirm the content is loaded.
            match_link_selector = 'a[href^="/matches/"]'
            print(f"Waiting for matches to appear on the page ('{match_link_selector}')...")
            page.wait_for_selector(match_link_selector, timeout=20000)
            
            print("Content is loaded. Extracting HTML...")
            html_content = page.content()
            browser.close()

        except Exception as e:
            print(f"\nAn error occurred during browser automation: {e}")
            return None

    # STEP 3: Parse the final HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    match_links = soup.select('a[href^="/matches/"]')
    
    if not match_links:
        print("No match links were found after loading the page.")
        return []

    print(f"\nFound {len(match_links)} matches on the page.")
    
    for link in match_links:
        team_name_elements = link.find_all('span', class_=lambda c: c and 'TeamName' in c)
        
        if len(team_name_elements) >= 2:
            home_team = team_name_elements[0].get_text(strip=True)
            away_team = team_name_elements[1].get_text(strip=True)
            all_matchups.append({"home": home_team, "away": away_team})

    return all_matchups

# --- Main execution part ---
if __name__ == "__main__":
    # Using your confirmed URL that correctly filters the view
    fotmob_url = "https://www.fotmob.com/leagues/78/matches/fifa-club-world-cup?group=by-round&round=3"
    
    matchups = scrape_round_of_16_matches(fotmob_url)

    if matchups:
        print("\n--- Round of 16 Matchups ---")
        for i, match in enumerate(matchups):
            print(f"Match {i+1}: {match['home']} vs {match['away']}")
        
        print("\n--- Raw JSON Output ---")
        print(json.dumps(matchups, indent=2))
    else:
        print("\nScraping failed or no matchups were found.")