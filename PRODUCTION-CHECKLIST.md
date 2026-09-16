# Cascade Painting — Production Checklist

## Before deploy
- Run `python build_site.py`.
- Run `python tools/site_audit.py`.
- Run `node --check public/assets/site.js`.
- Keep the existing `.git` directory when replacing project files.

## Cloudflare
- Build output: `public`.
- Functions directory: `functions`.
- Bind D1 as `DB` and apply `schema.sql` for a new database, or `migrations/0002_v4_production.sql` for an existing V3 database.
- Set `RATE_LIMIT_SALT` to a long random secret if D1 is connected.
- Configure Resend and/or `CRM_WEBHOOK_URL` so leads have a delivery path.

## Live launch checks
- Submit one real test lead on desktop and mobile.
- Click phone/email/estimate CTAs.
- Confirm Trustindex loads on Home and Reviews.
- Test `/404-test` and legacy redirects.
- Run PageSpeed Insights on Home, Interior Painting and Estimate.
- Run Google Rich Results Test on Home and one service page.
- In Search Console: inspect Home, submit `sitemap.xml`, and check indexing after the deployment is crawled.
- Confirm favicon and social share image on a messaging/social preview.

## Ongoing
- Add finished project photography as projects close.
- Publish resource content only when it answers a real homeowner question.
- Review search queries and landing-page conversions monthly before creating new location pages.
