# Cascade Painting V4 — Final Source Audit

Audit date: 2026-09-16

## Automated result

- 31 HTML files checked (including the 404 and noindex privacy page)
- 29 URLs in the XML sitemap
- all indexable pages have a single H1, title, meta description and canonical
- no duplicate titles, descriptions or canonicals found
- all internal page/image links resolve in the generated package
- all embedded images have alt text and explicit width/height
- all JSON-LD blocks parse as valid JSON
- XML sitemap and image sitemap parse successfully
- JavaScript syntax passes `node --check`
- Python build, enhancement layer and audit tool compile successfully

## Production optimization included

- full-bleed homepage hero retained
- live review feed remains directly under the hero
- owner/about story remains directly below reviews
- real project-story pages added
- homeowner resource center added
- service pages strengthened with scope factors, project proof and educational links
- estimate links from service pages carry service context
- estimate form restores in-session drafts and can preselect the originating service
- UTM/GCLID/referrer/landing-page attribution retained with leads
- first-party session-scoped conversion event endpoint added
- D1 schema extended for lead status, attribution and web events
- optional hashed-IP rate limiting added without storing raw IP addresses
- CSS/JS URLs are deployment-versioned so assets can use immutable caching safely
- Trustindex preconnect is removed from pages that do not use the widget
- GitHub Actions QA workflow added

## Checks that still require the live production URL

Source-level QA cannot substitute for these deployment checks:

1. Cloudflare response headers and redirects
2. end-to-end `/api/lead` delivery with the configured production bindings
3. D1 migration state
4. real Trustindex rendering from the production domain
5. PageSpeed/Core Web Vitals under live network conditions
6. Google Rich Results Test
7. Search Console indexing, sitemap processing and crawl diagnostics
8. actual social-link preview caching on third-party platforms

Use `PRODUCTION-CHECKLIST.md` immediately after deployment.
