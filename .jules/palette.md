## 2024-05-24 - Add ARIA labels to dashboard form elements
**Learning:** Missing `aria-label` on form inputs without visible `<label>` elements and on icon-only buttons causes accessibility issues for screen readers. In the GymBuddy dashboard, several inputs and buttons lacked accessible names.
**Action:** Always provide descriptive `aria-label` attributes for inputs and icon-only interactive elements when visible text labels are omitted for design reasons.
