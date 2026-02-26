from playwright.sync_api import sync_playwright
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Absolute path to the file
        file_path = os.path.abspath("dashboard/index.html")
        page.goto(f"file://{file_path}")

        # Verify title
        print(f"Page title: {page.title()}")

        # Scroll to demo section
        demo_section = page.locator("#demo")
        demo_section.scroll_into_view_if_needed()

        # Verify command cards are buttons
        cards = page.locator(".command-card")
        count = cards.count()
        print(f"Found {count} command cards")

        for i in range(count):
            card = cards.nth(i)
            tag_name = card.evaluate("el => el.tagName")
            print(f"Card {i} tag: {tag_name}")
            if tag_name != "BUTTON":
                print(f"ERROR: Card {i} is not a BUTTON")

            # Check inner span
            info = card.locator(".cmd-info")
            info_tag = info.evaluate("el => el.tagName")
            print(f"Card {i} info tag: {info_tag}")
            if info_tag != "SPAN":
                 print(f"ERROR: Card {i} info is not a SPAN")

        # Focus the first card to check styles
        first_card = cards.first
        first_card.focus()

        # Take screenshot
        os.makedirs("verification", exist_ok=True)
        page.screenshot(path="verification/ux_verification.png")
        print("Screenshot saved to verification/ux_verification.png")

        browser.close()

if __name__ == "__main__":
    run()
