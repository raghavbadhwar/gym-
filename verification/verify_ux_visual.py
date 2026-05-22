import os
from playwright.sync_api import sync_playwright

def verify_ux_visual():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        # Load the file
        filepath = os.path.join(os.getcwd(), 'dashboard/index.html')
        page.goto(f"file://{filepath}")

        # Scroll to Demo section
        page.locator("#demo").scroll_into_view_if_needed()

        # Focus on the first command card
        # Using .first because there are multiple buttons with this class
        # And I want to show the focus style
        card = page.locator(".command-card").first
        card.focus()

        # Take screenshot
        screenshot_path = "verification/ux_verification.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    verify_ux_visual()
