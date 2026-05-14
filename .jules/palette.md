## 2026-02-19 - Interactive Cards as Buttons
**Learning:** Interactive command cards (previously `<div>` with `onclick`) require conversion to `<button>` for keyboard accessibility, but must explicitly reset `appearance: none`, `text-align: left`, and `width: 100%` to match the existing design without disrupting layout.
**Action:** When converting custom card components to buttons, apply these CSS resets and ensure `:focus-visible` styles use `--border-glow` for consistency.
