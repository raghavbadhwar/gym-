import os
from playwright.sync_api import Page, expect, sync_playwright

def test_dashboard_accessibility(page: Page):
    """
    Verifies the accessibility changes made to dashboard/index.html
    """
    # 1. Arrange: Go to the dashboard
    file_path = f"file://{os.path.abspath('dashboard/index.html')}"
    page.goto(file_path)

    # 2. Act & Assert: Check for presence of elements using their ARIA labels

    # Check chat input
    chat_input = page.get_by_role("textbox", name="Type a message")
    expect(chat_input).to_be_visible()

    # Check send button
    send_button = page.get_by_role("button", name="Send message")
    expect(send_button).to_be_visible()

    # Open simulator to check modal buttons
    page.evaluate("openSimulator()")

    # Check phone input
    phone_input = page.get_by_role("textbox", name="Phone number")
    expect(phone_input).to_be_visible()

    # Check message input
    test_message_input = page.get_by_role("textbox", name="Test message")
    expect(test_message_input).to_be_visible()

    # Check close simulator button
    close_button = page.get_by_role("button", name="Close simulator")
    expect(close_button).to_be_visible()

    # 3. Screenshot: Capture the simulator modal with the changes
    os.makedirs("/home/jules/verification", exist_ok=True)
    page.screenshot(path="/home/jules/verification/verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_dashboard_accessibility(page)
            print("Successfully verified ARIA labels in dashboard!")
        except Exception as e:
            print(f"Error during verification: {e}")
            raise
        finally:
            browser.close()
