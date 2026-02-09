# Iron Mind API

Backend for the Iron Mind Kettlebell Academy, built with FastAPI and Google Cloud Firestore.

## Features
- **Courses & Lessons**: Public catalog and admin management.
- **Access Control**: Membership and course-specific entitlements.
- **Stripe Integration**: Checkout sessions and robust webhook handling.
- **Admin Interface**: CRUD operations, audit logging, and metrics.
- **Firebase Auth**: Secure authentication for users and admins.

## Setup

### 1. Prerequisites
- Python 3.9+
- Google Cloud SDK (for deployment)
- Firebase Project
- Stripe Account

### 2. Environment Variables
Copy `.env.example` to `.env` and configure:

| Variable | Description |
|---|---|
| `PROJECT_ID` | GCP Project ID |
| `ENV` | `dev` or `prod` |
| `FRONTEND_ORIGIN` | URL of the frontend (e.g., `http://localhost:5173`) |
| `ADMIN_UIDS` | Comma-separated list of Firebase UIDs for admin access |
| `STRIPE_SECRET_KEY` | Stripe Secret Key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook Signing Secret (`whsec_...`) |
| `STRIPE_PRICE_ID_...` | Price IDs for products |
| `FIREBASE_ADMIN_SDK_JSON_BASE64` | (Optional) Base64 encoded service account JSON for local auth verification |

### 3. Local Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Running the Server
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.

## Testing

### Authentication
To test protected endpoints, you need a Firebase ID Token.
1.  **Frontend**: Log in via the app and run `await firebase.auth().currentUser.getIdToken()` in the console.
2.  **Script**: Use the Firebase REST API or Admin SDK to generate a token.

### Access Control Endpoints
Check a user's entitlements and membership status.
```bash
# Get User Access Summary
curl -H "Authorization: Bearer <ID_TOKEN>" http://localhost:8000/access/me

# Check Specific Course Access
curl -H "Authorization: Bearer <ID_TOKEN>" http://localhost:8000/access/courses/<COURSE_ID>
```

### Admin Endpoints
Manage content (Admin UID required).
```bash
# List all courses
curl -H "Authorization: Bearer <ID_TOKEN>" http://localhost:8000/admin/courses

# Create a Course
curl -X POST -H "Authorization: Bearer <ID_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"titleHe": "New Course", "descriptionHe": "...", "type": "one_time"}' \
     http://localhost:8000/admin/courses
```

### Stripe Webhooks
Test webhook handling using the Stripe CLI.
1.  **Login**: `stripe login`
2.  **Forward**: `stripe listen --forward-to http://localhost:8000/webhooks/stripe`
3.  **Trigger**:
    ```bash
    stripe trigger checkout.session.completed
    ```
    *Note: Adjust `STRIPE_WEBHOOK_SECRET` in `.env` to match the CLI output secret.*

## Deployment
Deploy to Google Cloud Run:
```bash
gcloud run deploy api --source . --region us-central1 --allow-unauthenticated
```

## Common Issues

### 401 Unauthorized
- **Cause**: Missing or invalid `Authorization` header.
- **Fix**: Ensure header format is `Bearer <ID_TOKEN>`. Check token expiration.

### 403 Forbidden
- **Cause**: Valid token but insufficient permissions.
- **Fix**: For admin routes, add your UID to `ADMIN_UIDS`. For access routes, ensure valid purchase/subscription in Firestore.

### Webhook Signature Verification Failed (400)
- **Cause**: `STRIPE_WEBHOOK_SECRET` mismatch.
- **Fix**: When using `stripe listen`, it generates a *new* secret. Update your local `.env` with this secret.

### Firestore Permissions
- **Cause**: "Missing or insufficient permissions" error.
- **Fix**: Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set or run `gcloud auth application-default login`. Checks `app/config.py` for fallback project ID logic.
