## 2024-05-22 - Interactive Elements Semantics
**Learning:** Interactive command cards were implemented as `div`s, lacking keyboard accessibility (tab focus, enter/space activation).
**Action:** Use `<button>` for interactive cards with CSS resets (`appearance: none`, `text-align: left`, `width: 100%`) to ensure native accessibility while maintaining visual design.
