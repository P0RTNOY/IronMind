# Phase 7 Routing Verification

This document catalogs the verification commands, outputs, and checklists to ensure Phase 7.0 and 7.1 routing and deep-linking changes have been applied safely and function securely across the frontend UI.

## 1. Automated Grep Sweeps
These commands verify that the application has removed all manual string interpolated routes and solely relies on the canonical `routes.ts` helpers.

### Command Execution:
```bash
grep -RIn "/program/" apps/web || true
grep -RIn "#/courses/" apps/web || true
grep -RIn "#/lessons/" apps/web || true
grep -RIn "to={\`/courses\|to={\`/lessons\|window\.location\.hash" apps/web || true
```

### Expected Output Criteria:
- `apps/web/lib/routes.ts` should be the **only** file producing matches for string anchors (`#/courses/`, `#/lessons/`). 
- Occurrences within compiled `/dist` or `node_modules` folders are safe and anticipated. 
- No matches should exist in native project `.tsx` files.

---

## 2. API Backend Verification
Ensures the non-prod-only constraint remained isolated to the frontend and didn't disrupt the Python backend integration points.

### Command:
```bash
make test-api-ci
```

### Expected Output Criteria:
- All 114 test cases pass with `100%`.
- Exit code indicates `0` errors.

---

## 3. Manual Smoke Checklist
Verification requires launching the `apps/web` dev server (`npm run dev`) and executing the following checks in your local browser sandbox.

### Backward-Compatibility & Canonical Redirection (Phase 7.0)
- [ ] Open `http://localhost:5173/#/program/<id>` and verify it visually redirects to `/#/courses/<id>`.
- [ ] Hit the hardware/browser "Back" button after redirection. Confirm you do not enter a redirect loop with the original `/program/<id>` link.

### Deep-Link Error Handling & Global Fallbacks (Phase 7.1)
- [ ] Navigate to an inherently invalid route like `/#/foobar` and ensure it hits `<NotFound />` instead of silently bouncing to `/#/`.
- [ ] Target the `<NotFound />` view explicitly by accessing `/#/not-found`. Verify layout stability and functionality.
- [ ] Directly open a `/#/lessons/<id>` deep link as an **unauthenticated** visitor (incognito window). Confirm `LessonPlayer` gracefully issues a `401` error fetching playback and displays a **"Login"** CTA. 
- [ ] Open the same restricted lesson deep link as an **authenticated user lacking access entitlements**. Confirm it yields a `403` and displays a **"Purchase Access"** CTA.
- [ ] While in either `LessonPlayer` isolated error state, click the **"Back to Course"** CTA rendered underneath and verify correct navigation returning to `/#/courses/<course_id>`.
