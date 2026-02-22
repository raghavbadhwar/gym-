## 2026-05-23 - Interactive Command Cards
**Learning:** Command cards (like those in the demo section) were implemented as `div`s with `onclick` handlers, making them inaccessible to keyboard users and screen readers. Users rely on standard button behaviors (focus, enter key activation) for such interactive elements.
**Action:** Always implement interactive cards as `<button>` elements with proper CSS resets (`appearance: none`, `text-align: left`, etc.) to get accessibility for free. Convert inner block elements to spans to maintain valid HTML.
