## 2026-05-20 - Command Card Keyboard Accessibility
**Learning:** The dashboard's interactive command cards (`.command-card`) were implemented as `div` elements, making them inaccessible to keyboard users and screen readers.
**Action:** Always use `<button>` elements for interactive cards, resetting default styles (`appearance: none`, `text-align: left`, `width: 100%`) to maintain the card layout while gaining native focus and activation support.
