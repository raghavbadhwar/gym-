## 2024-05-22 - Handling Legacy onclick Divs
**Learning:** Command cards in this dashboard use `onclick` attributes without proper accessibility roles or keyboard support, requiring custom JS to bridge keyboard events.
**Action:** Use a utility function to attach keydown listeners (Enter/Space) to elements with `role="button"` that rely on inline `onclick` handlers, rather than refactoring to `<button>` which would break existing styles.
