## 2024-05-23 - Interactive Command Cards Pattern
**Learning:** Interactive elements like command cards were implemented as `div`s with `onclick`, making them inaccessible to keyboard users and screen readers.
**Action:** Converted `.command-card` to `<button>` elements with CSS resets (`appearance: none`, `text-align: left`, `width: 100%`) and added `:focus-visible` styles to provide clear visual feedback for keyboard navigation while preserving the original design. Inner content containers were changed from `div` to `span` to ensure valid HTML phrasing content within the button.
