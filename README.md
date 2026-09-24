# Cascade Painting — V4 Production Optimization

This is the production-oriented Cascade Painting website package: static-first, Cloudflare-ready, SEO-focused, conversion-measured, and prepared to feed a future CRM/mobile app through stable API contracts.

## Local preview

Open this project folder in VS Code and run Live Server. The included `.vscode/settings.json` uses `/public` as the web root.

## Rebuild + QA

```bash
python build_site.py
python tools/site_audit.py
node --check public/assets/site.js
```

`build_site.py` creates the base pages and automatically runs `v4_enhancements.py`, which adds the production optimization layer, project stories, homeowner resources, internal linking, analytics hooks and support files.

## Cloudflare Pages

- Repository root: this project folder
- Build command: `python build_site.py`
- Build output directory: `public`
- Functions directory: `functions`

If the current Cloudflare setup uses no build command, the already-generated `public` folder can still deploy. Using the build command is preferable because it ensures generated files stay synchronized.

## Lead delivery

`POST /api/lead` supports:

- D1 persistence through `DB`
- Resend notification email
- future CRM/app delivery through `CRM_WEBHOOK_URL`
- UTM/GCLID/referrer/landing-page attribution
- optional privacy-preserving submission rate limiting through `RATE_LIMIT_SALT`

For a fresh D1 database use `schema.sql`. For a database created from the previous version, use `migrations/0002_v4_production.sql`.

## First-party site measurement

`POST /api/event` can persist session-scoped events into D1. The browser code does not create cross-site IDs or advertising profiles. It measures page views, conversion clicks, meaningful scroll depth, form progression and successful leads so the future dashboard can show which pages actually create business.

## Content architecture

The build contains:

- primary service landing pages
- core local service-area pages
- direct Google Reviews links without a third-party widget
- real project journal + four full project stories
- homeowner resource hub + five substantial guides
- project/service/resource cross-linking
- multi-step estimate experience with in-session draft recovery

## App integration

See `APP-INTEGRATION.md`. The public site is ready to send normalized leads and source attribution to `app.cascadepaintingpa.com` without changing the public URL structure.

## Production launch

See `PRODUCTION-CHECKLIST.md` and `FINAL-AUDIT.md` before pushing live.
