## 2024-02-11 - Accessibility for Legacy Interactive Elements
**Learning:** Legacy interactive elements (e.g., `.command-card` divs) relying on inline `onclick` must use `role="button"`, `tabindex="0"`, and have keyboard listeners (Enter/Space) attached via `script.js` to trigger the click.
**Action:** When refactoring existing UI, always check for non-semantic elements with `onclick` handlers and upgrade them to accessible buttons.

## 2024-02-11 - Playwright Verification for Static Dashboard
**Learning:** Playwright verification for the static dashboard requires explicit viewport sizing and scrolling (e.g., `scroll_into_view_if_needed()`) to capture elements correctly, as standard `focus()` might not align the viewport for screenshots.
**Action:** Use `scroll_into_view_if_needed()` before taking screenshots in Playwright scripts for focused elements.
