## 2024-05-18 - Missing ARIA Labels on Form Inputs and Icon Buttons
**Learning:** Found a recurring pattern in the app's components where form inputs (especially within chat UIs or modals) lacked associated `<label>` tags or `aria-label` attributes, and icon-only buttons lacked text descriptions, which impacts screen reader accessibility.
**Action:** When implementing new form inputs or icon buttons without visual text, ensure an `aria-label` is always included.
