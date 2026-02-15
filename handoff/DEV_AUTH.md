# Development Authentication Strategy

To facilitate local development without requiring a full Firebase setup for every developer/environment, the backend supports a **Debug Authentication** mode.

## How it works

When the backend is running in `dev` mode (`ENV=dev`), it inspects incoming requests for specific headers *before* attempting to validate the standard Bearer token.

## Headers

| Header | Value | Description |
|---|---|---|
| `X-Debug-Uid` | `string` (e.g., "test-user") | The User ID to impersonate. If present, the backend treats the request as authenticated with this UID. |
| `X-Debug-Admin` | `"1"` | If set to "1", the impersonated user is granted **Admin** privileges. |

## Example Usage

### Admin Request
```bash
curl -H "X-Debug-Uid: test-admin" \
     -H "X-Debug-Admin: 1" \
     http://localhost:8080/admin/courses
```

### Regular User Request
```bash
curl -H "X-Debug-Uid: test-user" \
     http://localhost:8080/me
```

## Frontend Implementation

The frontend should store these values in `localStorage` (or similar) during development and inject them into every API request via a centralized fetch wrapper.
