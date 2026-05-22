## 2026-01-30 - Dashboard Accessibility
**Learning:** The static dashboard uses icon-only buttons for critical actions (Send, Close) without ARIA labels, and lacks loading states for async operations.
**Action:** Always verify icon-only buttons have `aria-label` and ensure async buttons have a disabled/loading state.
