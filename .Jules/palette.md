# Palette's Journal - UX & Accessibility Learnings

## 2026-02-02 - Chat Interface Accessibility
**Learning:** Adding `aria-label` to icon-only buttons is crucial but insufficient for custom interactive elements. Div-based "cards" (like command suggestions) are often keyboard-inaccessible.
**Action:** Always pair `role="button"` and `tabindex="0"` with a JavaScript `keydown` handler for Enter/Space keys when retrofitting accessibility onto `div` elements.
