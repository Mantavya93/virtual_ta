from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://tds.s-anand.net/#/2025-01/")
    page.wait_for_timeout(5000)

    # Extract all keys in window
    keys = page.evaluate("Object.keys(window)")
    print("🧠 Global window keys:")
    for key in keys:
        if "data" in key.lower():
            print(f" - {key}")

    browser.close()