# Cascade App / CRM Integration

The public site is now prepared to act as the acquisition layer for `app.cascadepaintingpa.com`.

## Lead contract
`POST /api/lead` creates a lead with customer/project fields plus landing page, source page, referrer, UTM parameters and GCLID. It can persist to D1, send email through Resend, and forward the same normalized lead to `CRM_WEBHOOK_URL`.

Recommended CRM lead stages: `new -> contacted -> estimate_scheduled -> estimate_sent -> won/lost -> scheduled -> completed -> review_requested`.

## First-party website events
`POST /api/event` can write session-scoped events to the D1 `web_events` table. Current events include page views, phone/email clicks, project/resource clicks, estimate CTA clicks, scroll depth, form progress and successful lead submission. No raw IP address is stored by this endpoint.

## D1
For a fresh database use `schema.sql`. For an existing V3 database apply `migrations/0002_v4_production.sql`, followed by `migrations/0003_google_reviews.sql`.

## Google Business Profile reviews
`GET /api/reviews` returns display-safe live Google review data to the Home and Reviews pages. `/api/google/start` and `/api/google/callback` own the OAuth flow; `/api/google/status` provides password-protected connection status. OAuth tokens are encrypted before D1 storage, and cached review content is encrypted in the `GOOGLE_REVIEWS_CACHE` KV namespace with automatic expiration. See `GOOGLE-REVIEWS-SETUP.md` for provisioning and authorization.

## Rate limiting
If `DB` and `RATE_LIMIT_SALT` are configured, the lead endpoint hashes the connecting IP with the private salt and limits repeated form submissions. The raw IP is not persisted.

## Next app phase
The app can consume the existing lead schema immediately, then add customer records, estimates, job scheduling, photos/files, products/colors, tasks, invoices, review automation, dashboards and crew/mobile workflows without changing public website URLs.
