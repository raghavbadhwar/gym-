## 2026-01-28 - Retrofitting Accessibility on Clickable Divs
**Learning:** Adding `role='button'` and `tabindex='0'` to `div`s with `onclick` handlers is a safe, low-risk way to retroactively make interactive elements accessible without breaking existing CSS that targets `div` elements.
**Action:** When retrofitting legacy or static sites, prefer attribute augmentation over tag replacement if CSS refactoring is out of scope.
