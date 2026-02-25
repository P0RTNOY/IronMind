# Dev Seeding

## What it does

`POST /admin/dev/seed` creates realistic demo content in Firestore:

- **2 Courses** — one `one_time`, one `subscription`, both published
- **6 Lessons** — 3 per course (Strength, Metcon, Mobility), first has a placeholder vimeo ID
- **4 Plans** — 2 per course, first has a placeholder PDF path
- **(Optional) 1 Entitlement** — for a debug user if `SEED_DEBUG_UID` is set

## How to invoke

```bash
# Admin auth required (debug headers in dev)
curl -X POST http://localhost:8080/admin/dev/seed \
  -H "X-Debug-Uid: my-uid" \
  -H "X-Debug-Admin: 1"

# Force overwrite existing docs
curl -X POST "http://localhost:8080/admin/dev/seed?force=1" \
  -H "X-Debug-Uid: my-uid" \
  -H "X-Debug-Admin: 1"
```

Or use the **"🌱 Seed Demo Data"** button in the Admin dashboard (dev mode only).

## Idempotency

Uses fixed document IDs (e.g. `course_demo_one_time`, `lesson_demo_course_demo_one_time_1`).

- **Without `?force=1`:** existing docs are skipped entirely.
- **With `?force=1`:** existing docs are updated with `merge=True`.

Returns `{"created": [...], "updated": [...], "skipped": [...]}`.

## Debug entitlement

Set `SEED_DEBUG_UID` in `.env` to automatically grant course access to a test user:

```env
SEED_DEBUG_UID=my-test-uid
```

## Production safety

- The route is **not mounted** when `ENV=prod`.
- The seed function raises `RuntimeError("seeding_disabled_in_prod")` if called directly.
