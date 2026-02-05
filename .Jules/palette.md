## 2024-05-22 - Keyboard Accessibility for Custom Elements
**Learning:** Custom interactive elements (like `div`s with `onclick`) are invisible to keyboard users. This is a common pattern in dashboard widgets.
**Action:** Always add `role="button"`, `tabindex="0"`, and a generic `keydown` handler when creating non-native interactive elements.
