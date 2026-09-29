# Cascade Painting — Production Checklist

## Before deploy
- Run `python build_site.py`.
- Run `python tools/site_audit.py`.
- Run `npm run check`.
- Run `npm test`.
- Keep the existing `.git` directory when replacing project files.

## Cloudflare
- Build output: `public`.
- Functions directory: `functions`.
- Bind D1 as `DB` and apply `schema.sql` for a new database, or migrations `0002` and `0003` in order for an existing V3 database.
- Create and bind a KV namespace as `GOOGLE_REVIEWS_CACHE`.
- Add the Google variables and encrypted secrets listed in `GOOGLE-REVIEWS-SETUP.md`.
- Set `RATE_LIMIT_SALT` to a long random secret if D1 is connected.
- Configure Resend and/or `CRM_WEBHOOK_URL` so leads have a delivery path.

## Live launch checks
- Submit one real test lead on desktop and mobile.
- Click phone/email/estimate CTAs.
- Complete the first authorization at `/api/google/start`.
- Confirm live cards load on Home and Reviews and their Google links open the discovered Business Profile.
- Check `/api/google/status` with the owner setup password.
- Test `/404-test` and legacy redirects.
- Run PageSpeed Insights on Home, Interior Painting and Estimate.
- Run Google Rich Results Test on Home and one service page.
- In Search Console: inspect Home, submit `sitemap.xml`, and check indexing after the deployment is crawled.
- Confirm favicon and social share image on a messaging/social preview.

## Ongoing
- Add finished project photography as projects close.
- Publish resource content only when it answers a real homeowner question.
- Review search queries and landing-page conversions monthly before creating new location pages.
