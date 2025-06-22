from playwright.sync_api import sync_playwright

url = "https://www.fotmob.com/leagues/78/table/fifa-club-world-cup"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, timeout=60000)
    page.wait_for_timeout(5000)  # wait for JS
    html = page.content()
    browser.close()

# Save the HTML to a file
with open("fotmob_table.html", "w", encoding="utf-8") as f:
    f.write(html)

print("HTML saved to fotmob_table.html")
