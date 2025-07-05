#!/usr/bin/env python3

from app import compute_joker_points, scrape_with_requests, scrape_quarters_with_requests

def test_joker_scoring():
    print("Testing joker scoring logic...")
    
    # Test cases based on actual matches
    test_cases = [
        ("Paris Saint-Germain vs Inter Miami CF: 4-0", "Should be correct (exact score)"),
        ("Paris Saint-Germain vs Inter Miami CF: 3-1", "Should be partial (correct winner)"),
        ("Inter Miami CF vs Paris Saint-Germain: 1-0", "Should be incorrect (wrong winner)"),
        ("Chelsea FC vs SL Benfica: 4-1", "Should be correct (exact score)"),
        ("Flamengo RJ vs Bayern München: 2-4", "Should be correct (exact score)"),
        ("Real Madrid vs Borussia Dortmund: 1-0", "Should be pending (match not finished)"),
    ]
    
    for joker_prediction, description in test_cases:
        points = compute_joker_points(joker_prediction, {})
        print(f"{joker_prediction} -> {points} points ({description})")

if __name__ == "__main__":
    test_joker_scoring() 