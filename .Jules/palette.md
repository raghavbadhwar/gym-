## 2026-02-01 - Missing ARIA on Icon Buttons
**Learning:** Icon-only buttons (like send/close) are frequently missing `aria-label` attributes in this codebase, making them inaccessible to screen readers.
**Action:** When adding or modifying icon-only buttons, always check for and add an appropriate `aria-label`.
