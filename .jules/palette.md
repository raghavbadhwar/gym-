## 2024-05-22 - Interactive Elements: Div vs Button
**Learning:** Using `div` for interactive elements (like command cards) requires extensive ARIA and JS polyfills for keyboard support, whereas `<button>` provides this natively but requires CSS resets.
**Action:** Default to `<button>` for all interactive elements and apply CSS resets to the component to maintain design flexibility without sacrificing accessibility.
