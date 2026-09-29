# Google Business Profile reviews setup

The website now uses Cloudflare Pages Functions for Google OAuth and review retrieval. OAuth credentials, encrypted tokens, and Google resource IDs stay on the server. The browser only calls `GET /api/reviews`.

## Google Cloud

Enable these APIs in the same Google Cloud project as the OAuth client:

- Google My Business API
- My Business Account Management API
- My Business Business Information API

Add this exact authorized redirect URI to the existing Web Application OAuth client:

`https://cascadepaintingpa.com/api/google/callback`

Keep `https://www.googleapis.com/auth/business.manage` on the consent screen. While the External app remains in Testing, Google normally expires this scope's refresh token after seven days. Move the app to Production after the connection is verified if ongoing access is required.

## Cloudflare resources

Reuse the existing D1 database bound as `DB`. Apply `migrations/0003_google_reviews.sql` to it. For a new database, `schema.sql` already contains every required table.

Create one Workers KV namespace for encrypted review cache content and bind it to the Pages project as `GOOGLE_REVIEWS_CACHE`. KV is used because each cached payload receives a 29-day automatic expiration, including when the site receives no traffic.

In Cloudflare, open **Workers & Pages → Cascade Painting project → Settings → Bindings** and add:

- D1 database binding: `DB` (the existing site database)
- KV namespace binding: `GOOGLE_REVIEWS_CACHE`

Add the values below under the production environment's variables and secrets, then redeploy. Use **Encrypt** for every credential or random secret.

| Name | Cloudflare type | Value |
| --- | --- | --- |
| `GOOGLE_CLIENT_ID` | Secret | Client ID from the Google OAuth Web Application |
| `GOOGLE_CLIENT_SECRET` | Secret | Client Secret from the same OAuth client |
| `GOOGLE_REDIRECT_URI` | Variable | `https://cascadepaintingpa.com/api/google/callback` |
| `GOOGLE_SETUP_PASSWORD` | Secret | A new random value with at least 32 characters |
| `GOOGLE_TOKEN_ENCRYPTION_KEY` | Secret | Exactly 32 random bytes encoded as Base64 |
| `GOOGLE_BUSINESS_NAME` | Variable | `Cascade Painting` |

Generate the two new secret values locally in PowerShell:

```powershell
$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
[Convert]::ToBase64String($bytes) # GOOGLE_TOKEN_ENCRYPTION_KEY

$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
[Convert]::ToBase64String($bytes) # GOOGLE_SETUP_PASSWORD
```

Save those values in a password manager. Do not put them in `.env.example`, source code, GitHub, support messages, or this chat. Changing the encryption key after connecting makes the stored tokens unreadable and requires a new Google authorization.

`GOOGLE_ACCOUNT_ID` and `GOOGLE_LOCATION_ID` are optional variables. Leave them unset on the first attempt. The callback discovers all accessible accounts and locations and selects one exact normalized title match for `Cascade Painting`. If more than one match exists, the setup page will ask for both IDs rather than selecting the wrong location.

## First authorization

1. Deploy the code, bindings, database migration, and environment values.
2. In a normal browser window, visit `https://cascadepaintingpa.com/api/google/start`.
3. Enter `GOOGLE_SETUP_PASSWORD`. It is submitted only to the same-origin Cloudflare Function.
4. Sign in with the Google account that manages Cascade Painting and approve Business Profile access.
5. Google returns to the callback and the page confirms the discovered business location.
6. Open `https://cascadepaintingpa.com/reviews/`. The first visit refreshes the encrypted cache and displays live reviews.
7. To inspect safe connection status later, visit `https://cascadepaintingpa.com/api/google/status` and enter the same setup password.

## Cache and failure behavior

The server fetches up to 50 most recently updated reviews and Google's own average rating and total count. Fresh data is reused for six hours. Concurrent refreshes use a database lease so normal traffic causes one Google request. Temporary Google failures use the last valid encrypted cache for up to 29 days and retry after 15 minutes. Expired or revoked authorization is retried after six hours and the owner status page requests reconnection. KV automatically deletes every cache payload before Google's 30-day Business Profile storage limit.

The public endpoint never returns OAuth tokens, the Client Secret, account IDs, location IDs, or upstream Google error bodies.
