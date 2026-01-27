# Palette's Journal

## 2024-05-22 - Initial Setup
**Learning:** This repo uses a simple HTML/CSS/JS structure for the dashboard, not a modern JS framework build chain.
**Action:** Adapt verification steps to check plain HTML/CSS/JS instead of running `pnpm test` or `pnpm lint`.

## 2024-05-22 - Accessibility Basics
**Learning:** Static HTML dashboards often miss basic accessibility attributes like `aria-label` on icon-only buttons and input fields, assuming visual context is enough.
**Action:** Always check icon-only buttons (like send/close) and inputs without explicit `<label>` tags for `aria-label` or `aria-labelledby`.
