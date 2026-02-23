## 2024-05-23 - Interactive Command Cards
**Learning:** Interactive cards that trigger actions (like "Demo Commands") must be implemented as native `<button>` elements, not `<div>`s with `onclick`.
**Action:** Use `<button type="button" class="card-btn">` and reset styles using CSS (`appearance: none`, `text-align: left`, `width: 100%`) to maintain visual design while gaining native keyboard accessibility (focus, enter/space activation).
