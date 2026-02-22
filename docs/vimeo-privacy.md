# Vimeo Privacy Settings

To ensure paid video content is only playable on our platform and cannot be embedded elsewhere, follow these steps for every video uploaded to Vimeo:

1. **Go to Vimeo Video Settings**.
2. Navigate to **Privacy** → **Where can this be embedded?**.
3. Select **Specific domains**.
4. Add the production domains:
   - `ironmind.app`
   - `www.ironmind.app`
5. *(Optional)* Set visibility to **Hide from Vimeo** so the video doesn't appear in public Vimeo searches.
6. *(Optional)* Under video settings, disable **Downloads**.

## Local Testing
Vimeo domain restrictions rely on the browser's `Referer`/`Origin` headers. While the backend defaults to allowing `http://localhost:5173` for payload fetching, the actual Vimeo iframe might block playback on `localhost` depending on Vimeo's current policies. 

If local playback is blocked:
- Use a tunneling service like [ngrok](https://ngrok.com/) or Cloudflare Tunnels to expose your local environment on a public domain, and add that tempoary domain to the Vimeo allowlist for testing.
- Do NOT add `localhost` to production Vimeo settings permanently.
