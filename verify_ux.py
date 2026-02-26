from playwright.sync_api import sync_playwright
import time

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto("http://localhost:8080/index.html")

    # Wait for page to load
    page.wait_for_load_state("networkidle")

    # 1. Verify ARIA labels
    send_btn = page.locator(".send-btn")
    # The modal close button is inside the modal, which is hidden initially, but exists in DOM
    close_btn = page.locator(".modal-close")

    print(f"Send button aria-label: {send_btn.get_attribute('aria-label')}")
    print(f"Close button aria-label: {close_btn.get_attribute('aria-label')}")

    assert send_btn.get_attribute("aria-label") == "Send message"
    assert close_btn.get_attribute("aria-label") == "Close simulator"

    # 2. Verify Command Cards attributes
    cards = page.locator(".command-card")
    count = cards.count()
    print(f"Found {count} command cards")
    assert count > 0
    for i in range(count):
        card = cards.nth(i)
        role = card.get_attribute("role")
        tabindex = card.get_attribute("tabindex")
        assert role == "button"
        assert tabindex == "0"

    # 3. Verify Keyboard Navigation & Focus Style
    first_card = cards.first
    first_card.scroll_into_view_if_needed()
    first_card.focus()

    # Take screenshot of the focused card to see the ring
    page.screenshot(path="verification_focus.png")

    # 4. Verify Keyboard Interaction (Enter key)
    # The 'hi' card is likely the first one
    print("Pressing Enter on first card...")
    page.keyboard.press("Enter")

    # Wait for interaction
    # The script scrolls to the phone mockup and sends a message
    time.sleep(2) # Wait for scroll and animation

    page.screenshot(path="verification_interaction.png")

    # Check if message was sent (outgoing message 'hi' should exist)
    outgoing = page.locator(".message.outgoing", has_text="hi")
    assert outgoing.count() > 0
    print("Outgoing message 'hi' found.")

    print("Verification complete!")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
