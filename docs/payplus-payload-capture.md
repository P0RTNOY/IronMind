# PayPlus Payload Capture Guide

In Phase 6.2A, we've implemented a mechanism to securely capture raw webhook payloads from PayPlus, even without live API credentials. This is vital for discovering the exact structure and field names of PayPlus's undocumented webhook responses before building out the final robust parser.

## How It Works

1. **Configuration:** The feature is toggled by `PAYPLUS_CAPTURE_WEBHOOK_PAYLOADS=true` in your environment.
2. **Redaction:** Before writing any data to the database, a strict redaction utility recursively sanitizes the raw JSON body to strip any PII.
   - Keys like `email`, `phone`, `full_name`, `cc`, and `cvv` are targeted.
   - Heuristics are used to catch loose 13–19 digit strings (potential PANs) or 3–4 digit strings (potential CVVs).
3. **Storage:** The sanitized payload is saved to the `payment_events` Firestore collection under the `payload_raw_redacted` property, avoiding pollution of standard schema values.

---

## Step-by-Step Local Debugging Workflow

To intercept a webhook locally, you must tunnel PayPlus's remote HTTP call to your local Docker backend.

### 1. Start Your Tunnel
Run a tunneling service to expose your local API port. For example, using `cloudflared`:

```bash
cloudflared tunnel --url http://localhost:8080
```
*(Copy the generated `https://...trycloudflare.com` URL)*

### 2. Configure Your Environment
Update your `.env` (or override when running `make dev`):

```bash
# Keep these as arbitrary non-empty strings so the app boots
PAYPLUS_API_KEY="local_debug"
PAYPLUS_SECRET_KEY="local_debug"

# Set the webhook base URL to your tunnel address
PUBLIC_WEBHOOK_BASE_URL="https://your-tunnel-url-here.trycloudflare.com"

# Ensure capture is enabled
PAYPLUS_CAPTURE_WEBHOOK_PAYLOADS=true
```

Restart your containers for the new Webhook URL to propagate to link generation API calls.

### 3. Trigger a Checkout
Go to the frontend, click "Checkout", and you will be redirected to the PayPlus sandbox UI.
Complete a successful test payment, or purposely fail one (failure callbacks are actively configured).

### 4. Inspect the Payload
Once PayPlus fires the webhook to your tunnel, the backend will process it, redact it, and save it.

You can view the captured payloads via the Admin Endpoint:
```bash
# Ensure you pass an Admin Header
curl -H "X-Debug-Admin: 1" "http://localhost:8080/admin/payments/events"
```

In the JSON response, inspect `payload_raw_redacted`. This will show you exactly what PayPlus sends, allowing you to update the `PayPlusProvider.verify_webhook` implementation with accurate models!
