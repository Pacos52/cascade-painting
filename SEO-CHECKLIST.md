# SEO / local-search implementation

## Built into the website

- unique title tag and meta description for every indexable page
- self-referencing canonical URLs
- semantic H1/H2 hierarchy
- crawlable HTML navigation and internal links
- LocalBusiness / HousePainter structured data with NAP, hours, contact point and service area
- Service structured data on service pages
- FAQ structured data only where matching FAQs are visible on-page
- Breadcrumb structured data on service/location pages
- WebPage schema with page-specific primary imagery
- service-area pages with unique, useful copy rather than mass doorway-page duplication
- real local project references where project evidence exists
- descriptive image alt text
- responsive WebP images and `srcset`
- explicit image dimensions to reduce layout shift
- hero image preload / fetch priority
- lazy loading on below-the-fold images
- direct Google Reviews links without a third-party review embed
- XML sitemap aligned only to indexable pages
- image sitemap tied to the landing pages where images appear
- robots.txt
- expanded legacy URL redirects
- page-specific 1200×630 Open Graph / Twitter images
- favicon and web app manifest
- mobile-first responsive layout
- keyboard-accessible navigation, controls and form labels
- visible focus states and improved text contrast
- security headers and cache rules appropriate for stable asset filenames
- `llms.txt` with concise machine-readable company/service context
- consistent business name, address and phone throughout the site
- first-touch UTM/referrer/GCLID attribution retained through the estimate journey
- no self-serving LocalBusiness aggregate-rating markup

## External actions after deployment

These require the production domain or account access and cannot be fully validated from source code alone:

1. Submit `/sitemap.xml` in Google Search Console and Bing Webmaster Tools.
2. Verify the preferred canonical domain and apex/`www` HTTPS redirects.
3. Keep Google Business Profile name/address/phone/services consistent with the website.
4. Add the exact Facebook business URL only after it is confirmed; do not guess a profile URL.
5. Add GA4 / Google Ads conversion IDs when the actual property IDs are known. The frontend already exposes conversion events and retains campaign attribution.
6. Connect `/api/lead` to D1, Resend and/or the CRM webhook and test a real lead.
7. Confirm the Google Reviews links still open the correct Business Profile after any profile or URL change.
8. Keep adding original project photography and substantive project/location notes instead of generating thin city pages at scale.
9. Run PageSpeed Insights/Lighthouse on the deployed site to measure real CDN and third-party behavior.

No source-code change can guarantee a search ranking. This build is designed to remove common technical and content-architecture weaknesses while keeping the content useful to actual homeowners.
