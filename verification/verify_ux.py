import os
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load the file
        file_path = os.path.abspath('dashboard/index.html')
        page.goto(f'file://{file_path}')

        # Verify aria-label on Send button
        send_btn = page.locator('button.send-btn')
        aria_label = send_btn.get_attribute('aria-label')
        print(f"Send button aria-label: {aria_label}")
        if aria_label != "Send message":
            print("ERROR: Send button missing aria-label")

        # Verify aria-label on Close button
        close_btn = page.locator('button.modal-close')
        aria_label_close = close_btn.get_attribute('aria-label')
        print(f"Close button aria-label: {aria_label_close}")
        if aria_label_close != "Close modal":
            print("ERROR: Close button missing aria-label")

        # Verify Command Cards are buttons
        cards = page.locator('.command-card')
        count = cards.count()
        print(f"Found {count} command cards")

        # Check tag name
        first_card = cards.first
        tag_name = first_card.evaluate("el => el.tagName.toLowerCase()")
        print(f"First command card tag: {tag_name}")
        if tag_name != "button":
            print("ERROR: Command card is not a button")

        # Verify focus state
        # Scroll to demo section
        page.locator('#demo').scroll_into_view_if_needed()

        # Focus the first card
        first_card.focus()

        # Check if focus-visible style is applied (this is hard to check programmatically without visual reg, but we can check computed style)
        # Note: :focus-visible might not be triggered by .focus() in some browsers/playwright without keyboard interaction.
        # We will simulate Tab key
        page.keyboard.press("Tab") # Focuses first focusable element?
        # Actually, let's just click somewhere else then Tab into it?
        # Or just assume focus() works for screenshot if we set force=True?
        # Better: Press Tab until we hit a command card.

        # Let's reset focus to body
        page.focus("body")
        # Tab through to command cards. They are in #demo section.
        # It might take many tabs.

        # Let's just focus explicitly and take screenshot.
        first_card.focus()

        # Take screenshot of the demo section
        page.locator('#demo').screenshot(path='verification/demo_section_focus.png')
        print("Screenshot saved to verification/demo_section_focus.png")

        browser.close()

if __name__ == "__main__":
    run()
