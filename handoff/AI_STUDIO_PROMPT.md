You are building a Next.js (App Router) frontend for the API described in the attached OpenAPI spec.
Requirements:

Use TypeScript.

Create a minimal API client wrapper src/lib/api.ts using fetch.

Base URL configurable via NEXT_PUBLIC_API_BASE_URL (default http://localhost:8080).

Frontend Architecture:
- Use **Tailwind CSS** and **shadcn/ui** (optional but preferred).
- Use **Client Components** for API calls because auth headers (X-Debug-Uid) come from localStorage.
- Use Server Components only where it makes sense (e.g., layouts, public data if possible without auth).
- Implement a `useAuth()` hook that reads `debugUid` and `debugAdmin` from localStorage.
- All requests MUST go through a centralized `apiFetch()` wrapper that injects:
    - Base URL
    - `X-Debug-Uid` header
    - `X-Debug-Admin` header (if admin)
- Do NOT hardcode endpoints; use the paths exactly as defined in the OpenAPI spec.
- Assume backend CORS allows origin `http://localhost:3000`.

**API Wrapper Contract:**
Create a single `apiFetch<T>(path: string, init?: RequestInit): Promise<{ data: T | null, error: any, status: number }>` helper that:
1.  Prepends `NEXT_PUBLIC_API_BASE_URL`.
2.  **Client-Side Guard:** Ensure getting headers from localStorage only happens in the browser (`typeof window !== 'undefined'`).
3.  Injects `X-Debug-Uid` and `X-Debug-Admin` headers from localStorage if available.
4.  **Content-Type Handling:** If `init.body` is `FormData`, let the browser set the Content-Type (do NOT force application/json). Otherwise, default to `application/json`.
5.  Performs the fetch.
6.  Parses JSON response safely.
7.  Returns an object `{ data, error, status }` - DO NOT THROW on 4xx/5xx status codes (only network errors).
8.  **Path Safety:** The `path` argument MUST be a relative path starting with `/` (e.g., `/courses`). Do NOT accept full URLs to prevent double-prepending the base URL.

**Client-Side Rule:**
- `useAuth()` and `apiFetch()` must only run in files marked with `'use client'`.
- Always guard `typeof window !== 'undefined'` before accessing `localStorage` to prevent SSR crashes.
- **Hydration Safety:** Use `useEffect` to read `localStorage` and set auth state. Do NOT read `localStorage` during the initial render (even with window checks) to avoid hydration mismatches.
- **Admin Gating:** Use `/access/me` to determine admin status (preferred). Note that `/access/me` returns `isAdmin` while `/me` returns `is_admin`. If a user visits `/admin` and is NOT an admin, redirect to `/` immediately.

**Critical Error Handling:**
- `/access/courses/{course_id}` returns 403 status code when access is denied (it does NOT return `{ allowed: false }`). You must check `status === 403` to show "Purchase Required".
- 401 Unauthorized -> Redirect to `/dev-auth`.

Auth: In local dev, do NOT use Firebase. Instead, store debugUid and debugAdmin in localStorage and send these headers on every request:

X-Debug-Uid: <uid>

X-Debug-Admin: 1 (optional)

Build pages:

/ Home: show published courses from GET /courses

/courses/[id]: load course via GET /courses/{course_id}; before showing protected content call GET /access/courses/{course_id}; if 403 show “purchase required”

/search: query GET /search?q=...

/me: show GET /me

/access: show GET /access/me

/admin: admin dashboard:

list courses GET /admin/courses

create/update/publish/unpublish

metrics GET /admin/metrics/overview

Handle errors nicely:

401 → show “Not authenticated” and link to /dev-auth

403 → show “Access denied”

404 → show “Not found”

Add a /dev-auth page: input debugUid + toggle admin, save to localStorage.

UI can be simple: Tailwind + basic cards/forms.
