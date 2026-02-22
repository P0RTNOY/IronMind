# Deploying to Cloud Run

This guide outlines how to seamlessly deploy the IronMind API to Google Cloud Run natively utilizing best practices.

## Prerequisites
- A Google Cloud Project.
- The `gcloud` CLI installed and authenticated.
- Enable the **Cloud Run** API and **Secret Manager** API.

## Environment Variables
The application distinguishes explicitly between development (`dev`) and production (`prod`). In production, it executes a strict fast-fail validation upon boot guaranteeing correct configuration. Ensure you map the following correctly in your environment.

### 1. Hardened Execution (Required)
When deploying, the `--set-env-vars` must specify:
- `ENV` = `prod`
- `PROJECT_ID` = `your-gcp-project`

Because the environment is strictly set to `prod`, the API expects certain values and **will instantly crash on startup** if they are omitted:
- `PAYPLUS_API_KEY`: Production credentials for Payplus
- `PAYPLUS_SECRET_KEY`: Production credentials for Payplus
- `PUBLIC_WEBHOOK_BASE_URL`: Public-facing domain hitting this identical Cloud Run instance (Used strictly by Webhooks validation). E.g: `https://api.ironmind.app`

*(Note: If `VIMEO_VERIFY_ENABLED=true` is provided, `VIMEO_ACCESS_TOKEN` is similarly strictly enforced).* 

### 2. Secret Manager (Highly Recommended)
We recommend mapping all your production keys specifically via Secret Manager instead of raw ENV injections:
```sh
gcloud run deploy ironmind-api \
  --image gcr.io/your-project/ironmind-api:latest \
  --set-env-vars ENV=prod,PROJECT_ID=your-project,PUBLIC_WEBHOOK_BASE_URL=https://... \
  --set-secrets PAYPLUS_API_KEY=payplus-key:latest,PAYPLUS_SECRET_KEY=payplus-secret:latest
```

## Operations & Telemetry

### Application Probes
You should correctly configure the health probes built explicitly for platform orchestration (they are intentionally excluded from Auth requirements):
- **Liveness probe:** `/healthz`
- **Readiness probe:** `/readyz`

### Request IDs & Logs
Every HTTP response processed by the Cloud Run instance guarantees an `X-Request-Id` header (even if it 500s mid-flight). Furthermore, stdout structural logs are aggregated by StackDriver, embedding this explicit `request_id` context directly onto every log record emitted by the app enabling full-stack causality.
