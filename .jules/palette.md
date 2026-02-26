## 2026-02-14 - Interactive Cards Pattern
**Learning:** The dashboard used `div` with `onclick` for interactive cards. While visually fine, this breaks keyboard navigation and screen reader support. Converting them to `<button>` elements requires resetting default button styles (`appearance: none`, `text-align: left`, `width: 100%`) to maintain the card layout.
**Action:** When encountering clickable cards, always prefer `<button>` over `div` + `onclick`. Use a reset utility class or specific CSS rule to strip default button styling while keeping the semantic benefits.
