# Palette's Journal - Critical Learnings

## 2024-05-18 - [Pattern Changes: Button Conversions]
**Learning:** Modifying standard HTML patterns, like converting `div` elements to `span` inside native `<button>` elements, is necessary to ensure valid HTML5 phrasing content within interactive command cards (e.g., `.command-card`).
**Action:** When creating or converting custom interactive elements to semantic `<button>`s, always audit child elements to ensure they use valid phrasing content (like `span`) rather than block-level elements (like `div`) to maintain strict HTML5 compliance and improve screen reader compatibility.

## 2024-05-18 - [Focus State Visibility]
**Learning:** Interactive elements require explicit focus states for keyboard navigation. Using `:focus-visible` ensures clear visual feedback for keyboard users while preserving standard mouse interaction styles without unwanted focus rings.
**Action:** Always verify focus rings using the keyboard (e.g., Tab key). Apply `:focus-visible` pseudo-class, and when possible, utilize existing design system variables (like `--border-glow`) to create consistent and accessible focus indicators.
