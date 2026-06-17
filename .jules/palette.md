## 2024-03-05 - Missing ARIA Labels on Interactive Elements
**Learning:** Found a recurring pattern in the `dashboard` static site where icon-only buttons (like the chat send button and modal close button) and input fields without visible `<label>` elements were lacking `aria-label` attributes, making them inaccessible to screen readers.
**Action:** Always verify that all icon-only buttons and form inputs have appropriate `aria-label` or `aria-labelledby` attributes during UI implementation and code reviews to ensure screen reader accessibility.
