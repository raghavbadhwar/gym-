## 2026-02-08 - Interactive Command Cards
**Learning:** The dashboard uses `div` elements with `onclick` for interactive cards (e.g., Command Cards) without keyboard support (`role="button"`, `tabindex="0"`). This pattern repeats for other interactive elements.
**Action:** When creating new interactive cards, always add `role="button"`, `tabindex="0"`, and a `keydown` handler (or use `<button>` if styling permits).
