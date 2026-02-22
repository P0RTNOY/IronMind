# Vimeo Privacy Verification

Phase 2.7 introduces automated verification of Vimeo video privacy settings.
When an Admin clicks **Verify Privacy** via the Lesson UI, the backend uses the Vimeo API to check the video's embedded privacy setting and the exact whitelisted domains.

## Requirements

The background verification service requires a valid Vimeo API token. The feature is disabled by default in development unless explicit environment variables are set.

### 1. Generating a Vimeo Token

1. Go to the [Vimeo Developer Portal](https://developer.vimeo.com/apps).
2. Create a new App (or use an existing one for your IronMind account).
3. Under **Authentication**, create a new **Personal Access Token**.
4. **Scopes Required**: Generate the token with permissions to read video privacy and domains.
   - Typically, selecting `Public`, `Private`, and `Interact` is sufficient.
   - *Note:* If the verification endpoint returns `403 Forbidden` for fetching domains, you may need to adjust token scopes based on Vimeo's current UI and your account tier.

### 2. Environment Variables

Set the following in your production environment (e.g., Google Cloud Run secrets or local `.env`):

```bash
# Enable verification
VIMEO_VERIFY_ENABLED=true

# Your Personal Access Token from Vimeo
VIMEO_ACCESS_TOKEN=xxxxxxxxx

# Comma-separated list of exact domains required
VIMEO_REQUIRED_EMBED_ORIGINS=ironmind.app,www.ironmind.app
```

### 3. Verification Logic

The service performs the following checks:
1. Validates that `privacy.embed` is either `"whitelist"` or `"domains"`.
2. Fetches the allowed domains from Vimeo (`/videos/{id}/privacy/domains`).
3. Compares the list case-insensitively against `VIMEO_REQUIRED_EMBED_ORIGINS`.
4. If there are **any missing domains**, the video is marked as "Failed" and the specific missing domains are displayed in the Admin UI.
