## 2026-02-17 - Interactive Command Cards
**Learning:** Interactive `div` elements should be replaced with native `<button>` elements to improve keyboard accessibility and screen reader support. However, this requires careful CSS resets (e.g., `appearance: none`, `text-align: left`, `width: 100%`) to maintain the original layout.
**Action:** Always pair semantic HTML refactoring with CSS resets and explicit `:focus-visible` styles (e.g., using `--border-glow`) to ensure both accessibility and visual consistency.
