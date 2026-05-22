## 2024-05-23 - Interactive Card Pattern
**Learning:** Interactive cards (like the command examples) were originally implemented as `div`s with `onclick`, making them inaccessible to keyboard users. Converting them to `<button>` elements with CSS resets (`appearance: none`, `text-align: left`, etc.) makes them semantic and keyboard-accessible without breaking the visual design.
**Action:** Always implement interactive "cards" or list items as `<button>` or `<a>` elements, not `div`s. Use CSS resets to strip default button styling and apply custom styles. Ensure inner content is phrasing content (e.g., `span`) if using `<button>`.

## 2024-05-23 - Focus Visibility
**Learning:** Standard `:focus` styles can be obtrusive for mouse users. Using `:focus-visible` ensures that focus indicators (like a ring or border color change) only appear for keyboard users or when necessary, providing a cleaner experience for mouse users while maintaining accessibility.
**Action:** Use `:focus-visible` instead of `:focus` for custom interactive components to provide keyboard focus feedback without affecting mouse interaction.
