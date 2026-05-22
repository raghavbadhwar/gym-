## 2024-05-21 - Interactive Card Pattern
**Learning:** Interactive cards (like command shortcuts) implemented as `div`s lack native keyboard accessibility. Converting them to `<button>` elements provides free tab navigation and activation (Enter/Space) but requires specific CSS resets to maintain the card aesthetic.
**Action:** Use `<button>` for interactive cards with `appearance: none`, `text-align: left`, `width: 100%`, and ensure inner content is phrasing content (e.g., use `span` instead of `div` inside).
