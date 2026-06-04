import os
import sys
from playwright.sync_api import sync_playwright

def main():
    dashboard_path = os.path.abspath('dashboard/index.html')
    url = f"file://{dashboard_path}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # Check #chatInput
        chat_input = page.locator('#chatInput')
        if chat_input.get_attribute('aria-label') != 'Type a message':
            print("Failed: #chatInput missing correct aria-label")
            sys.exit(1)

        # Check .send-btn
        send_btn = page.locator('.send-btn')
        if send_btn.get_attribute('aria-label') != 'Send message':
            print("Failed: .send-btn missing correct aria-label")
            sys.exit(1)

        # Check simulator elements
        # Open simulator
        page.evaluate('openSimulator()')
        page.wait_for_selector('#simulatorModal.active', state='visible')

        # Check #testPhone
        test_phone = page.locator('#testPhone')
        if test_phone.get_attribute('aria-label') != 'Test phone number':
            print("Failed: #testPhone missing correct aria-label")
            sys.exit(1)

        # Check #testMessage
        test_msg = page.locator('#testMessage')
        if test_msg.get_attribute('aria-label') != 'Test message':
            print("Failed: #testMessage missing correct aria-label")
            sys.exit(1)

        # Check .modal-close
        modal_close = page.locator('.modal-close')
        if modal_close.get_attribute('aria-label') != 'Close simulator':
            print("Failed: .modal-close missing correct aria-label")
            sys.exit(1)

        print("All ARIA labels verified successfully!")
        browser.close()

if __name__ == '__main__':
    main()
