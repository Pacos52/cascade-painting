from pathlib import Path
import json, html, re
from datetime import date

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT/'public'
manifest = json.loads((PUBLIC/'images/image-manifest.json').read_text())

SITE = {
    'name':'Cascade Painting',
    'domain':'https://cascadepaintingpa.com',
    'phone':'267-461-4367',
    'phone_href':'+12674614367',
    'email':'paxton@cascadepaintingpa.com',
    'address':'24 Green St, Lansdale, PA 19446',
    'google_maps':'https://www.google.com/maps/search/?api=1&query=Cascade+Painting',
    'google_address':'https://www.google.com/maps/search/?api=1&query=24+Green+St+Lansdale+PA+19446',
}

def rel(depth, path=''):
    prefix = '../'*depth
    if path in ('','/'):
        return prefix or './'
    return prefix + path.lstrip('/')

def picture(name, alt, depth=0, cls='', loading='lazy', fetchpriority=None, sizes='(max-width: 720px) 100vw, 50vw'):
    variants = manifest[name]
    srcset = ', '.join(f"{rel(depth,'images/'+v['file'])} {v['width']}w" for v in variants)
    largest = variants[-1]
    attrs = []
    if cls: attrs.append(f'class="{cls}"')
    attrs.append(f'alt="{html.escape(alt, quote=True)}"')
    attrs.append(f'width="{largest["width"]}" height="{largest["height"]}"')
    attrs.append(f'src="{rel(depth,"images/"+largest["file"])}"')
    attrs.append(f'srcset="{srcset}" sizes="{sizes}"')
    if loading: attrs.append(f'loading="{loading}"')
    attrs.append('decoding="async"')
    if fetchpriority: attrs.append(f'fetchpriority="{fetchpriority}"')
    return '<img ' + ' '.join(attrs) + '>'

def business_schema():
    data = {
      '@context':'https://schema.org',
      '@graph':[
        {
          '@type':['HomeAndConstructionBusiness','HousePainter'],
          '@id': SITE['domain']+'/#business',
          'name':'Cascade Painting',
          'url':SITE['domain']+'/',
          'logo':SITE['domain']+'/images/logo.png',
          'image':SITE['domain']+'/images/hero-kitchen-1600.webp',
          'telephone':'+1-267-461-4367',
          'email':SITE['email'],
          'description':'Veteran and family-owned painting company serving Lansdale, North Wales, Ambler, Blue Bell, Maple Glen and surrounding Montgomery County communities.',
          'slogan':'Not your typical contractor experience.',
          'address':{
            '@type':'PostalAddress','streetAddress':'24 Green St','addressLocality':'Lansdale','addressRegion':'PA','postalCode':'19446','addressCountry':'US'
          },
          'areaServed':[{'@type':'City','name':x} for x in ['Lansdale, PA','North Wales, PA','Ambler, PA','Blue Bell, PA','Maple Glen, PA','Horsham, PA','Plymouth Meeting, PA','Willow Grove, PA']],
          'hasMap':SITE['google_address'],
          'contactPoint':{'@type':'ContactPoint','telephone':'+1-267-461-4367','email':SITE['email'],'contactType':'customer service','areaServed':'US','availableLanguage':'English'},
          'openingHoursSpecification':[
            {'@type':'OpeningHoursSpecification','dayOfWeek':['Monday','Tuesday','Wednesday','Thursday','Friday'],'opens':'07:00','closes':'19:00'},
            {'@type':'OpeningHoursSpecification','dayOfWeek':'Saturday','opens':'09:00','closes':'17:00'}
          ],
          'knowsAbout':['Interior painting','Exterior painting','Cabinet refinishing','Drywall repair','Wallpaper removal','Concrete floor coatings','Commercial painting','Line striping']
        },
        {
          '@type':'WebSite','@id':SITE['domain']+'/#website','url':SITE['domain']+'/', 'name':'Cascade Painting','publisher':{'@id':SITE['domain']+'/#business'}, 'inLanguage':'en-US'
        }
      ]
    }
    return data

def service_schema(title, description, canonical, faq=None):
    graph = business_schema()['@graph'][:]
    graph.append({
        '@type':'Service','@id':canonical+'#service','name':title,'description':description,
        'provider':{'@id':SITE['domain']+'/#business'},
        'areaServed':{'@type':'AdministrativeArea','name':'Montgomery County, Pennsylvania'},
        'url':canonical
    })
    if faq:
        graph.append({'@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in faq]})
    return {'@context':'https://schema.org','@graph':graph}

def breadcrumbs_schema(items):
    return {'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i+1,'name':name,'item':url} for i,(name,url) in enumerate(items)]}

def head(title, desc, path, depth=0, image='hero-living-room-1600.webp', schema=None, extra_schema=None, preload=None, indexable=True):
    canonical = SITE['domain'] + path
    robots = 'index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1' if indexable else 'noindex,follow'
    schemas = [schema or business_schema()]
    schemas.append({
      '@context':'https://schema.org','@type':'WebPage','@id':canonical+'#webpage','url':canonical,
      'name':title,'description':desc,'isPartOf':{'@id':SITE['domain']+'/#website'},
      'about':{'@id':SITE['domain']+'/#business'},'publisher':{'@id':SITE['domain']+'/#business'},
      'primaryImageOfPage':{'@type':'ImageObject','url':SITE['domain']+'/images/'+image},'inLanguage':'en-US'
    })
    if extra_schema: schemas.append(extra_schema)
    schema_html = ''.join(f'<script type="application/ld+json">{json.dumps(x,separators=(",",":"))}</script>' for x in schemas)
    pre = ''
    if preload:
        family = next((k for k,v in manifest.items() if isinstance(v,list) and any(i['file']==preload for i in v)), None)
        if family:
            variants = manifest[family]
            srcset = ', '.join(f"{rel(depth,'images/'+v['file'])} {v['width']}w" for v in variants)
            pre = f'<link rel="preload" as="image" href="{rel(depth,"images/"+preload)}" imagesrcset="{srcset}" imagesizes="100vw" fetchpriority="high">'
        else:
            pre = f'<link rel="preload" as="image" href="{rel(depth,"images/"+preload)}" fetchpriority="high">'
    family = next((k for k,v in manifest.items() if isinstance(v,list) and any(i['file']==image for i in v)), None)
    social_file = f'og-{family}.jpg' if family and (PUBLIC/'images'/f'og-{family}.jpg').exists() else 'og-cascade.jpg'
    social_image = SITE['domain'] + '/images/' + social_file
    social_alt = f'Cascade Painting project photography for {title.split("|")[0].strip()}'
    review_assets = ''
    if path in ('/', '/reviews/'):
        review_assets = f'<link rel="stylesheet" href="{rel(depth,"assets/google-reviews.css")}?v=20260928"><script src="{rel(depth,"assets/google-reviews.js")}?v=20260930" defer></script>'
    return f'''<!doctype html><html lang="en-US"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc, quote=True)}"><meta name="robots" content="{robots}"><link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#143746"><meta name="color-scheme" content="light"><meta name="format-detection" content="telephone=no">
<meta property="og:type" content="website"><meta property="og:locale" content="en_US"><meta property="og:site_name" content="Cascade Painting"><meta property="og:title" content="{html.escape(title, quote=True)}"><meta property="og:description" content="{html.escape(desc, quote=True)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{social_image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:type" content="image/jpeg"><meta property="og:image:alt" content="{html.escape(social_alt, quote=True)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{html.escape(title, quote=True)}"><meta name="twitter:description" content="{html.escape(desc, quote=True)}"><meta name="twitter:image" content="{social_image}"><meta name="twitter:image:alt" content="{html.escape(social_alt, quote=True)}">
<link rel="icon" href="{rel(depth,'images/favicon.png')}" sizes="96x96" type="image/png"><link rel="apple-touch-icon" href="{rel(depth,'images/apple-touch-icon.png')}"><link rel="manifest" href="{rel(depth,'site.webmanifest')}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">{pre}<link rel="stylesheet" href="{rel(depth,'assets/site.css')}">{review_assets}{schema_html}</head>'''

def header(depth=0, active=''):
    links=[('Services','services/'),('Projects','projects/'),('Our Standard','our-standard/'),('About','about/'),('Service Areas','service-areas/'),('Reviews','reviews/')]
    nav=''.join(f'<a {"aria-current=\"page\"" if label==active else ""} href="{rel(depth,p)}">{label}</a>' for label,p in links)
    return f'''<body><a class="skip-link" href="#main">Skip to content</a><div class="topline"><div class="wrap topline-inner"><span>Veteran & family owned · Montgomery County, PA</span><span>Interior · Exterior · Cabinets · Coatings</span></div></div><header class="site-header" data-header><div class="wrap header-inner"><a class="brand" href="{rel(depth)}" aria-label="Cascade Painting home"><img src="{rel(depth,'images/logo.png')}" width="488" height="289" alt="Cascade Painting" decoding="async"></a><nav class="desktop-nav" aria-label="Primary">{nav}</nav><div class="header-actions"><a class="phone-link" href="tel:{SITE['phone_href']}">{SITE['phone']}</a><a class="btn btn-primary btn-small" href="{rel(depth,'estimate/')}">Request an Estimate</a><button class="menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-menu" data-menu-toggle><span></span><span></span></button></div></div></header><div class="mobile-menu" id="mobile-menu" data-mobile-menu aria-hidden="true"><nav aria-label="Mobile primary">{nav}</nav><div class="mobile-menu-actions"><a href="tel:{SITE['phone_href']}" class="btn btn-ghost">Call {SITE['phone']}</a><a href="{rel(depth,'estimate/')}" class="btn btn-primary">Request an Estimate</a></div></div>'''

def footer(depth=0):
    return f'''<footer class="site-footer"><div class="wrap footer-grid"><div class="footer-brand"><img src="{rel(depth,'images/logo-footer.png')}" width="488" height="289" alt="Cascade Painting" loading="lazy" decoding="async"><p>Veteran and family-owned painting company based in Lansdale and serving communities throughout Montgomery County, Pennsylvania.</p><a class="text-link light-link" href="{rel(depth,'estimate/')}">Start a project →</a></div><div class="footer-col"><span>Services</span><a href="{rel(depth,'interior-painting-lansdale-pa/')}">Interior Painting</a><a href="{rel(depth,'exterior-painting-lansdale-pa/')}">Exterior Painting</a><a href="{rel(depth,'cabinet-refinishing-lansdale-pa/')}">Cabinet Refinishing</a><a href="{rel(depth,'wallpaper-removal-drywall-repair/')}">Drywall & Wallpaper</a><a href="{rel(depth,'floor-coatings-lansdale-pa/')}">Floor Coatings</a><a href="{rel(depth,'commercial-painting-lansdale-pa/')}">Commercial Painting</a></div><div class="footer-col"><span>Company</span><a href="{rel(depth,'projects/')}">Projects</a><a href="{rel(depth,'our-standard/')}">Our Standard</a><a href="{rel(depth,'about/')}">About</a><a href="{rel(depth,'reviews/')}">Reviews</a><a href="{rel(depth,'service-areas/')}">Service Areas</a></div><div class="footer-col"><span>Contact</span><a href="tel:{SITE['phone_href']}">{SITE['phone']}</a><a href="mailto:{SITE['email']}">{SITE['email']}</a><a href="{SITE['google_address']}" target="_blank" rel="noopener noreferrer">{SITE['address']}</a><p>Mon–Fri 7 AM–7 PM<br>Sat 9 AM–5 PM</p></div></div><div class="wrap footer-bottom"><span>© <span data-year></span> Cascade Painting</span><div><a href="{rel(depth,'privacy/')}">Privacy</a></div></div></footer><div class="mobile-cta" aria-label="Quick contact"><a href="tel:{SITE['phone_href']}">Call</a><a href="{rel(depth,'estimate/')}">Request Estimate</a></div><script src="{rel(depth,'assets/site.js')}" defer></script></body></html>'''

def page_shell(title, desc, path, depth, body, active='', image='hero-living-room-1600.webp', schema=None, extra_schema=None, preload=None, indexable=True):
    return head(title,desc,path,depth,image,schema,extra_schema,preload,indexable) + header(depth,active) + f'<main id="main">{body}</main>' + footer(depth)

def write(path, content):
    p=PUBLIC/path
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(content,encoding='utf-8')


def google_reviews_feed():
    return '<div class="wrap google-reviews-live"><p class="google-reviews-status" data-reviews-status role="status" aria-live="polite" aria-atomic="true">Customer reviews are available on Google.</p><ul class="google-reviews-grid" data-reviews-list aria-label="Recent Google customer reviews" hidden></ul></div>'

# HOME
home_body = f'''
<section class="hero-home hero-home-full"><div class="hero-full-media">{picture('hero-kitchen','Finished Cascade Painting kitchen and cabinetry project in Montgomery County, Pennsylvania',0,'hero-main-image','eager','high','100vw')}</div><div class="hero-full-shade" aria-hidden="true"></div><div class="wrap hero-full-inner"><div class="hero-full-copy"><p class="eyebrow hero-eyebrow">Cascade Painting · Lansdale & Montgomery County, Pennsylvania</p><h1><span>Not your typical contractor</span><em>experience.</em></h1><p class="hero-lead">Preparation-first painting, clear communication and beautiful finish work — handled with the care your home deserves.</p><div class="hero-actions"><a class="btn btn-hero-primary" href="estimate/">Request an Estimate <span>↗</span></a><a class="btn btn-hero-secondary" href="projects/">Explore Our Work</a></div></div><div class="hero-full-bottom"><div class="hero-proof"><span class="stars" data-review-hero-rating hidden></span><strong>Google reviews</strong><small data-review-hero-count>Customer feedback on Google</small></div><div class="hero-proof"><strong>Veteran & family owned</strong><small>Local ownership. Direct accountability.</small></div><div class="hero-proof"><strong>Preparation first</strong><small>The finish starts underneath.</small></div><div class="hero-project-note"><span>Featured project</span><strong>Kitchen & cabinetry</strong></div></div></div></section>

<section class="review-band" id="reviews" data-google-reviews data-review-limit="3"><div class="wrap review-band-head"><div><p class="eyebrow light">Reputation, not marketing copy</p><h2>What clients say after the ladders come down.</h2></div><div class="review-band-aside"><p>Recent public feedback from our Google Business Profile.</p></div></div><div class="wrap google-review-card"><div><span>Google Reviews</span><strong data-review-summary>See the latest feedback from Cascade clients.</strong><p data-review-summary-detail>Reviews open on Cascade Painting’s public Google Business Profile.</p></div><a class="btn btn-outline-light" data-review-link href="{SITE['google_maps']}" target="_blank" rel="noopener noreferrer">Read reviews on Google ↗</a></div>{google_reviews_feed()}</section>

<section class="feature-story home-about"><div class="wrap feature-story-grid"><div class="feature-story-copy"><p class="eyebrow">Owner-led by design</p><h2>Local accountability is part of the finish.</h2><p>Cascade Painting is veteran and family owned, based in Lansdale and intentionally focused on the communities around us. The company is built around a clear point of accountability, disciplined preparation and communication that stays straightforward from estimate through final walkthrough.</p><div class="story-facts"><div><strong>Veteran & family owned</strong><span>Service, responsibility and pride in the work.</span></div><div><strong>Lansdale based</strong><span>Focused on Montgomery County and nearby communities.</span></div><div><strong>Preparation driven</strong><span>Repairs and surface readiness are treated as finish quality.</span></div></div><a class="text-link" href="about/">More about Cascade →</a></div><div class="feature-story-media">{picture('dining-room','Finished dining room painted by Cascade Painting in North Wales, Pennsylvania',0,'','lazy',None,'(max-width: 980px) 100vw, 48vw')}<div class="story-card"><span>How we work</span><strong>Owner-led</strong><small>Local · accountable · detail driven</small></div></div></div></section>

<section class="service-lab"><div class="wrap service-lab-grid"><div class="service-preview" data-service-preview>{picture('living-room-alt','Finished residential interior painting project by Cascade Painting',0,'service-preview-img','lazy',None,'(max-width: 980px) 100vw, 42vw')}<div class="service-preview-caption"><span data-service-caption>Interior painting</span><small>Crafted for the way the room is actually lived in.</small></div></div><div class="service-menu"><p class="eyebrow">What we do</p><h2>One standard.<br>Different surfaces.</h2>
<a class="service-menu-row is-active" href="interior-painting-lansdale-pa/" data-service-src="images/living-room-alt-1920.webp" data-service-srcset="images/living-room-alt-640.webp 640w, images/living-room-alt-960.webp 960w, images/living-room-alt-1280.webp 1280w, images/living-room-alt-1600.webp 1600w, images/living-room-alt-1920.webp 1920w" data-service-label="Interior painting"><span>01</span><strong>Interior Painting</strong><i>Walls · ceilings · trim</i><b>↗</b></a>
<a class="service-menu-row" href="exterior-painting-lansdale-pa/" data-service-src="images/deck-1920.webp" data-service-srcset="images/deck-640.webp 640w, images/deck-960.webp 960w, images/deck-1280.webp 1280w, images/deck-1600.webp 1600w, images/deck-1920.webp 1920w" data-service-label="Exterior painting"><span>02</span><strong>Exterior Painting</strong><i>Siding · trim · decks</i><b>↗</b></a>
<a class="service-menu-row" href="cabinet-refinishing-lansdale-pa/" data-service-src="images/cabinets-1254.webp" data-service-srcset="images/cabinets-640.webp 640w, images/cabinets-960.webp 960w, images/cabinets-1254.webp 1254w" data-service-label="Cabinet refinishing"><span>03</span><strong>Cabinet Refinishing</strong><i>Doors · frames · islands</i><b>↗</b></a>
<a class="service-menu-row" href="wallpaper-removal-drywall-repair/" data-service-src="images/drywall-1920.webp" data-service-srcset="images/drywall-640.webp 640w, images/drywall-960.webp 960w, images/drywall-1280.webp 1280w, images/drywall-1600.webp 1600w, images/drywall-1920.webp 1920w" data-service-label="Drywall & surface repair"><span>04</span><strong>Drywall & Surface Repair</strong><i>Repairs · wallpaper removal</i><b>↗</b></a>
<a class="service-menu-row" href="floor-coatings-lansdale-pa/" data-service-src="images/garage-1920.webp" data-service-srcset="images/garage-640.webp 640w, images/garage-960.webp 960w, images/garage-1280.webp 1280w, images/garage-1600.webp 1600w, images/garage-1920.webp 1920w" data-service-label="Floor coatings"><span>05</span><strong>Floor Coatings</strong><i>Garages · basements</i><b>↗</b></a>
<a class="service-menu-row" href="commercial-painting-lansdale-pa/" data-service-src="images/basement-1000.webp" data-service-srcset="images/basement-640.webp 640w, images/basement-960.webp 960w, images/basement-1000.webp 1000w" data-service-label="Commercial painting"><span>06</span><strong>Commercial Painting</strong><i>Interiors · exteriors · line striping</i><b>↗</b></a>
</div></div></section>

<section class="project-reel-section"><div class="wrap reel-heading"><div><p class="eyebrow">Selected spaces</p><h2>Cascade at work.</h2></div><div class="reel-controls" aria-label="Project gallery controls"><button type="button" data-reel-prev aria-label="Previous projects">←</button><button type="button" data-reel-next aria-label="Next projects">→</button></div></div><div class="project-reel" data-project-reel>
<article class="reel-card">{picture('living-room-wide','Freshly painted bright living room with skylights and fireplace by Cascade Painting',0,'', 'lazy',None,'70vw')}<div><span>North Wales · Interior</span><h3>Light, quiet, finished.</h3></div></article>
<article class="reel-card">{picture('dining-room','Finished dining room with crisp walls, trim and warm hardwood floors by Cascade Painting',0,'','lazy',None,'70vw')}<div><span>North Wales · Interior</span><h3>Classic details, cleaner palette.</h3></div></article>
<article class="reel-card">{picture('kitchen','Bright kitchen and cabinetry project completed by Cascade Painting',0,'','lazy',None,'70vw')}<div><span>Kitchen · Cabinetry</span><h3>Precision where you see it every day.</h3></div></article>
<article class="reel-card">{picture('deck','Exterior deck staining and finish project by Cascade Painting',0,'','lazy',None,'70vw')}<div><span>Exterior · Deck</span><h3>A finish built for the weather.</h3></div></article>
<article class="reel-card">{picture('garage','Finished garage with painted walls, trim and coated floor by Cascade Painting',0,'','lazy',None,'70vw')}<div><span>Garage · Coatings</span><h3>Utility can still look intentional.</h3></div></article>
<article class="reel-card">{picture('basement','Finished basement with fresh walls and gray coated concrete floor by Cascade Painting',0,'','lazy',None,'70vw')}<div><span>Basement · Coatings</span><h3>Clean, durable, usable.</h3></div></article>
</div><div class="wrap reel-footer"><a class="btn btn-ghost" href="projects/">View the project journal</a></div></section>

<section class="standard-band"><div class="wrap standard-band-intro"><p class="eyebrow light">The Cascade Standard</p><h2>Professional work should feel professional.</h2><p>Not just at the end. At every point you interact with the company.</p></div><div class="wrap standard-band-grid"><article><span>01</span><h3>Clear scope</h3><p>We define what is being painted, repaired and protected before the project starts.</p></article><article><span>02</span><h3>Disciplined prep</h3><p>Protection, patching, sanding and surface readiness come before finish coats.</p></article><article><span>03</span><h3>Owner-led communication</h3><p>You know who to contact, what is happening and what comes next.</p></article><article><span>04</span><h3>Final walkthrough</h3><p>We review the work together and close the project with the same attention it started with.</p></article></div><div class="wrap standard-band-link"><a class="btn btn-outline-light" href="our-standard/">Explore our process</a></div></section>

<section class="local-section"><div class="wrap local-grid"><div><p class="eyebrow">Local by design</p><h2>Based in Lansdale. Working across the communities around it.</h2><p>We focus on Montgomery County and nearby areas so estimating, scheduling and follow-through stay practical and the service stays personal.</p><a class="btn btn-ghost" href="service-areas/">Explore service areas</a></div><div class="local-cities"><a href="painting-contractor-lansdale-pa/"><span>01</span><strong>Lansdale</strong><small>Home base</small></a><a href="service-areas/north-wales-pa/"><span>02</span><strong>North Wales</strong><small>Featured projects</small></a><a href="service-areas/ambler-pa/"><span>03</span><strong>Ambler</strong><small>Residential painting</small></a><a href="service-areas/blue-bell-pa/"><span>04</span><strong>Blue Bell</strong><small>Residential painting</small></a><a href="service-areas/maple-glen-pa/"><span>05</span><strong>Maple Glen</strong><small>Featured projects</small></a><a href="service-areas/"><span>06</span><strong>More communities</strong><small>View all areas</small></a></div></div></section>

<section class="faq-section"><div class="wrap faq-grid"><div><p class="eyebrow">Questions worth asking</p><h2>What homeowners usually want to know first.</h2></div><div class="faq-list"><details><summary>What types of projects are the best fit for Cascade?</summary><p>Interior and exterior painting, cabinet refinishing, drywall and surface repair, wallpaper removal, garage and basement floor coatings, and select commercial work throughout Montgomery County.</p></details><details><summary>How do estimates work?</summary><p>Start with a few project details. We will confirm fit, discuss the scope, and schedule an on-site visit when needed so the estimate reflects the actual surfaces and conditions.</p></details><details><summary>Do you handle prep and repairs before painting?</summary><p>Yes. Surface preparation is one of the most important parts of the job. The exact repair scope is defined before work begins so the finish is built on a sound surface.</p></details><details><summary>Can I see real project work before deciding?</summary><p>Yes. The project journal uses real Cascade project photography, including work from North Wales, Maple Glen and other nearby communities.</p></details></div></div></section>

<section class="final-cta"><div class="wrap final-cta-grid"><div><p class="eyebrow">Start with a conversation</p><h2>Your home should feel better when the project is over — and so should you.</h2></div><div><p>Tell us what you want to change. We will help you define the next step without turning the first conversation into a sales pitch.</p><div class="hero-actions"><a class="btn btn-primary" href="estimate/">Request an Estimate <span>↗</span></a><a class="text-link" href="tel:{SITE['phone_href']}">Call {SITE['phone']}</a></div></div></div></section>
'''
write(Path('index.html'), page_shell(
    'Cascade Painting | Painter in Lansdale & Montgomery County, PA',
    'Veteran and family-owned painter serving Lansdale and Montgomery County, PA for interior, exterior, cabinets, drywall repair, floor coatings and commercial work.',
    '/',0,home_body, image='hero-kitchen-1600.webp', preload='hero-kitchen-1671.webp'))

# Shared content builders

def page_hero(eyebrow, h1, lead, image_name, alt, depth=1, cta=True):
    buttons = f'<div class="hero-actions"><a class="btn btn-primary" href="{rel(depth,"estimate/")}">Request an Estimate <span>↗</span></a><a class="text-link" href="tel:{SITE["phone_href"]}">Call {SITE["phone"]}</a></div>' if cta else ''
    return f'''<section class="page-hero"><div class="wrap page-hero-grid"><div><p class="eyebrow">{eyebrow}</p><h1>{h1}</h1><p class="page-lead">{lead}</p>{buttons}</div><div class="page-hero-media">{picture(image_name,alt,depth,'','eager','high','(max-width: 980px) 100vw, 48vw')}<span class="media-corner">Real Cascade project</span></div></div></section>'''

def proof_rail(depth=1):
    return '''<section class="proof-rail"><div class="wrap proof-grid"><div><strong>Preparation first</strong><span>Protection, repair and surface readiness before finish coats.</span></div><div><strong>Clear communication</strong><span>Scope, schedule and expectations kept visible.</span></div><div><strong>Owner-led accountability</strong><span>A local business with a direct point of contact.</span></div><div><strong>Respect for the space</strong><span>Clean work areas and a deliberate closeout.</span></div></div></section>'''

def inline_cta(depth=1, heading='Ready to talk through your project?'):
    return f'''<section class="inline-cta"><div class="wrap inline-cta-grid"><h2>{heading}</h2><div><p>Share the basics and we will help you define the next step.</p><a class="btn btn-primary" href="{rel(depth,'estimate/')}">Request an Estimate <span>↗</span></a></div></div></section>'''

def faq_html(faq):
    return '<div class="faq-list">' + ''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in faq) + '</div>'

services = [
    {
      'slug':'interior-painting-lansdale-pa','title':'Interior Painting in Lansdale, PA | Cascade Painting','h1':'Interior painting that changes how the room feels — without making the project feel chaotic.','eyebrow':'Interior painting · Montgomery County','lead':'Walls, ceilings, trim, doors and complete interior repaints handled with careful protection, thoughtful prep and a clean finish.','image':'living-room-wide','alt':'Bright living room interior painting project completed by Cascade Painting in North Wales, Pennsylvania','desc':'Interior painting in Lansdale and Montgomery County, PA for walls, ceilings, trim and complete room refreshes. Veteran and family-owned Cascade Painting.','intro':'A good interior project is part finish work and part logistics. Furniture, floors, trim, transitions, repairs and daily cleanup all affect whether the experience feels controlled. Cascade approaches the room as a system, not a wall with color on it.','bullets':['Walls, ceilings, trim and doors','Drywall patching and surface repair','Wallpaper removal and wall preparation','Color and finish guidance','Occupied-home protection and cleanup'],'faq':[('Do you paint occupied homes?','Yes. Protection, daily cleanup and communication are built into the scope so the project can move forward with less disruption.'),('Can you repair drywall before painting?','Yes. Patching, repair and surface correction can be included when the existing condition requires it.'),('Do you remove wallpaper?','Yes. Wallpaper removal and the wall preparation needed afterward can be part of the project scope.'),('What areas do you serve?','Cascade is based in Lansdale and works throughout nearby Montgomery County communities including North Wales, Ambler, Blue Bell, Maple Glen, Horsham, Plymouth Meeting and surrounding areas.')],
      'gallery':[('den','Finished den after interior repaint by Cascade Painting'),('dining-room','Finished dining room after interior painting by Cascade Painting'),('bedroom','Bedroom with blue accent wall after Cascade Painting interior project')]
    },
    {
      'slug':'exterior-painting-lansdale-pa','title':'Exterior Painting in Lansdale, PA | Cascade Painting','h1':'Exterior painting built around the surface, the weather and what has to last.','eyebrow':'Exterior painting · Montgomery County','lead':'Thoughtful preparation and exterior coatings for siding, trim, doors, decks and other painted or stained surfaces.','image':'deck','alt':'Finished exterior deck coating project completed by Cascade Painting','desc':'Exterior painting and deck finishing in Lansdale and Montgomery County, PA with preparation-first service from Cascade Painting.','intro':'Exterior work is where shortcuts show up fastest. Exposure, moisture, old coatings and substrate condition all matter. We start by understanding what is actually on the surface before deciding what needs to happen next.','bullets':['Exterior siding and trim','Doors, shutters and architectural details','Deck staining and coatings','Scraping, sanding and spot priming','Caulking and minor surface preparation'],'faq':[('Do you paint aluminum siding?','Yes. Existing painted aluminum siding can often be prepared and repainted when the substrate is in suitable condition.'),('Do you stain decks?','Yes. Deck coating and staining projects are evaluated based on the condition of the wood and the existing finish.'),('How do you handle exterior prep?','Prep can include washing, scraping, sanding, caulking and priming as required by the surface and coating system.'),('When is exterior painting season in Pennsylvania?','Scheduling depends on temperature, moisture and product requirements. We plan exterior work around conditions that allow the coating to perform as intended.')],
      'gallery':[('deck','Finished deck coating by Cascade Painting'),('kitchen','Cascade Painting detail work'),('maple-glen','Cascade Painting local project')]
    },
    {
      'slug':'cabinet-refinishing-lansdale-pa','title':'Cabinet Refinishing in Lansdale, PA | Cascade Painting','h1':'Cabinet refinishing that makes the room feel new without replacing the room.','eyebrow':'Cabinet refinishing · Montgomery County','lead':'A controlled refinishing process for cabinet doors, frames and islands with close attention to prep, smoothness and durability.','image':'cabinets','alt':'Refinished kitchen cabinets and island by Cascade Painting','desc':'Cabinet painting and refinishing in Lansdale and Montgomery County, PA. Update kitchens and built-ins with Cascade Painting.','intro':'Cabinet work is less forgiving than a wall. Edges, door faces, hardware areas and high-touch surfaces put the finish under a microscope. The process has to be controlled enough that the final result feels deliberate up close.','bullets':['Kitchen cabinet doors and frames','Islands and built-ins','Degreasing and surface preparation','Priming and finish coating','Hardware removal and organized reassembly'],'faq':[('Is cabinet refinishing cheaper than replacing cabinets?','It can be a practical alternative when the existing boxes and doors are in good condition and the main goal is a finish or color change.'),('Do you remove cabinet doors?','The exact workflow depends on the project, but doors and hardware are typically handled in a way that allows controlled prep and finishing.'),('How durable is a painted cabinet finish?','Durability depends on the substrate, preparation and coating system. We match the process to the cabinet condition and intended use.'),('Can you paint an island a different color?','Yes. Two-tone kitchens, including contrasting islands, can be included in the project design.')],
      'gallery':[('cabinets','Refinished kitchen cabinets by Cascade Painting'),('kitchen','Finished kitchen painting project by Cascade Painting'),('dining-room','Interior finish work by Cascade Painting')]
    },
    {
      'slug':'commercial-painting-lansdale-pa','title':'Commercial Painting in Lansdale, PA | Cascade Painting','h1':'Commercial painting with the same discipline we bring into a home.','eyebrow':'Commercial painting · Montgomery County','lead':'Painting, coatings and select line striping for offices, shops, properties and other commercial environments where schedule and coordination matter.','image':'basement','alt':'Large finished commercial-like interior space with fresh walls and coated floor by Cascade Painting','desc':'Commercial painting in Lansdale and Montgomery County, PA for interiors, exteriors, coatings and select line striping.','intro':'Commercial work has a different set of constraints: access, operating hours, sequencing, drying time and the need to keep people moving safely around the work. We build the scope around those realities instead of treating the job like a larger house.','bullets':['Interior and exterior commercial painting','Tenant-turn and property refresh work','Concrete and floor coatings','Select line striping','Phased scheduling and occupied-space coordination'],'faq':[('Can work be phased around business hours?','Yes. Scheduling and access requirements are discussed during estimating so the work can be planned around the site.'),('Do you offer line striping?','Select line striping can be included in commercial scopes. The surface, layout and traffic requirements are reviewed before pricing.'),('Can you coat concrete floors?','Yes. Garage, basement and select commercial floor coating projects can be evaluated as part of the scope.'),('Do you provide written scopes for commercial work?','Yes. Clear scope definition is especially important for commercial projects and is built into the estimating process.')],
      'gallery':[('basement','Finished large interior with coated floor by Cascade Painting'),('garage','Garage floor coating and wall painting by Cascade Painting'),('garage-alt','Finished garage painting and coating project by Cascade Painting')]
    },
    {
      'slug':'floor-coatings-lansdale-pa','title':'Floor Coatings in Lansdale, PA | Cascade Painting','h1':'Concrete floor coatings that make utility spaces feel finished.','eyebrow':'Garage & basement coatings · Montgomery County','lead':'Durable-looking, easy-to-maintain floor coating systems for garages, basements and select commercial spaces.','image':'garage','alt':'Finished garage with gray floor coating and crisp painted walls by Cascade Painting','desc':'Garage and basement concrete floor coatings in Lansdale and Montgomery County, PA from Cascade Painting.','intro':'A floor coating changes more than the color of concrete. It changes how the entire garage or basement feels. The surface has to be evaluated, cleaned and prepared so the finish can bond and perform as intended.','bullets':['Garage floor coatings','Basement concrete coatings','Surface cleaning and preparation','Wall and trim painting for complete space refreshes','Select commercial floor coating projects'],'faq':[('Can you coat an older concrete floor?','Often, yes. The condition of the concrete, existing coatings, moisture and surface contamination all affect whether and how the floor should be coated.'),('Do you also paint garage walls and ceilings?','Yes. Garage projects can include walls, ceilings, trim and related finish work along with the floor.'),('How long before the floor can be used?','Return-to-service time depends on the coating system and site conditions. We provide the product-specific timing with the project plan.'),('Do you coat basement floors?','Yes. Basement concrete can be evaluated for coating as long as the surface conditions are suitable.')],
      'gallery':[('garage','Finished garage floor coating by Cascade Painting'),('garage-alt','Garage with painted walls and coated floor by Cascade Painting'),('basement','Finished basement with coated concrete floor by Cascade Painting')]
    },
    {
      'slug':'wallpaper-removal-drywall-repair','title':'Drywall Repair & Wallpaper Removal | Cascade Painting','h1':'The finish only looks as good as the surface underneath it.','eyebrow':'Wallpaper removal & drywall repair','lead':'Wallpaper removal, drywall repair, patching and surface preparation integrated into the painting process.','image':'drywall','alt':'Ceiling drywall repair project prepared for paint by Cascade Painting in North Wales, Pennsylvania','desc':'Wallpaper removal and drywall repair in Lansdale and Montgomery County, PA as part of professional painting projects.','intro':'Walls and ceilings rarely arrive ready for paint. Old wallpaper, settlement cracks, patches, openings and previous repairs can all telegraph through a new finish. We address the surface first so the paint is not being asked to hide a repair problem.','bullets':['Wallpaper removal','Drywall patching and repair','Ceiling repair','Hole and opening repair','Sanding, priming and surface preparation'],'faq':[('Can you paint immediately after wallpaper removal?','Sometimes additional cleaning, skim work, sanding or priming is needed. The wall is evaluated after removal before the finish plan is set.'),('Do you repair ceiling openings?','Yes. Ceiling and drywall repair can be included when openings, patches or damage need to be restored before painting.'),('Can you blend repaired areas into existing walls?','The goal is to make the repair read as part of the surface, but the exact process depends on texture, sheen, lighting and the extent of the repair.'),('Is drywall repair priced separately?','Repair work is defined in the scope so you can see what is being addressed before painting begins.')],
      'gallery':[('drywall','Ceiling drywall repair prepared for finish paint'),('maple-glen','Finished room after wallpaper removal and painting'),('living-room-wide','Finished interior paint project by Cascade Painting')]
    }
]

for svc in services:
    faq=svc['faq']
    path=f"/{svc['slug']}/"
    canonical=SITE['domain']+path
    body = page_hero(svc['eyebrow'],svc['h1'],svc['lead'],svc['image'],svc['alt']) + proof_rail() + f'''
<section class="content-section"><div class="wrap content-grid"><div class="prose-block"><p class="eyebrow">How we approach it</p><h2>Good finish work starts long before the final coat.</h2><p class="lead-copy">{svc['intro']}</p><div class="bullet-panel">{''.join(f'<div><span>✓</span><p>{b}</p></div>' for b in svc['bullets'])}</div></div><aside class="quote-card"><p class="eyebrow">A better contractor experience</p><h3>Clear scope. Careful prep. Direct communication.</h3><p>The project should feel organized before anyone opens a paint can.</p><a class="btn btn-primary" href="../estimate/">Request an Estimate</a></aside></div></section>
<section class="project-gallery-section"><div class="wrap"><div class="section-title-row"><div><p class="eyebrow">Real Cascade work</p><h2>See the finish in real spaces.</h2></div><a class="text-link" href="../projects/">More projects →</a></div><div class="editorial-gallery">{''.join(f'<figure>{picture(n,a,1,"","lazy",None,"(max-width: 760px) 100vw, 33vw")}<figcaption>{a}</figcaption></figure>' for n,a in svc['gallery'])}</div></div></section>
<section class="faq-section"><div class="wrap faq-grid"><div><p class="eyebrow">Frequently asked</p><h2>Details before you decide.</h2></div>{faq_html(faq)}</div></section>''' + inline_cta()
    schema=service_schema(svc['title'].split('|')[0].strip(),svc['desc'],canonical,faq)
    bread=breadcrumbs_schema([('Home',SITE['domain']+'/'),(svc['title'].split('|')[0].strip(),canonical)])
    write(Path(svc['slug'])/'index.html', page_shell(svc['title'],svc['desc'],path,1,body,'Services',image=f"{svc['image']}-{manifest[svc['image']][-1]['width']}.webp",schema=schema,extra_schema=bread,preload=manifest[svc['image']][-1]['file']))

# Services overview
service_cards=''.join(f'''<a class="service-overview-card" href="../{s['slug']}/"><span>{i:02d}</span><h2>{s['title'].split(' in ')[0]}</h2><p>{s['lead']}</p><b>Explore service ↗</b></a>''' for i,s in enumerate(services,1))
services_body=page_hero('Painting services','The right process for the surface in front of us.','Interior, exterior, cabinets, repairs, floor coatings and commercial work — all held to the same expectation for preparation and communication.','kitchen','Bright completed kitchen project by Cascade Painting',1)+f'''<section class="service-overview"><div class="wrap service-overview-grid">{service_cards}</div></section>'''+inline_cta()
write(Path('services/index.html'),page_shell('Painting Services in Lansdale, PA | Cascade Painting','Interior, exterior, cabinet refinishing, drywall repair, floor coatings and commercial painting services in Montgomery County, PA.','/services/',1,services_body,'Services',image='kitchen-1600.webp'))

# Projects page
projects_body=page_hero('Project journal','A portfolio should prove how the work feels — not just fill a grid.','Real Cascade Painting projects from Montgomery County and nearby communities. Browse finished interiors, exterior work, repairs and floor coatings photographed on real jobs.','living-room-wide','Finished North Wales living room by Cascade Painting',1)+f'''
<section class="project-stories"><div class="wrap"><div class="project-page-intro"><p class="eyebrow">What to look for</p><p>Look past the color alone. Consistent lines, clean transitions, repaired surfaces, protected adjacent finishes and an even final sheen are the details that separate a quick repaint from deliberate finish work.</p></div><article class="project-story feature"><div class="project-story-media">{picture('living-room-wide','Finished North Wales living room after interior painting by Cascade Painting',1,'','lazy',None,'(max-width: 980px) 100vw, 60vw')}</div><div class="project-story-copy"><span>North Wales, PA · Interior painting</span><h2>Brightening a multi-room interior without flattening the character.</h2><p>Walls, ceilings, trim and repaired surfaces were brought into a cleaner, quieter palette so the existing architecture, hardwood and natural light could carry the room.</p><a class="text-link" href="../service-areas/north-wales-pa/">Painting in North Wales →</a></div></article>
<div class="project-story-grid"><article>{picture('dining-room','Finished North Wales dining room by Cascade Painting',1,'','lazy',None,'(max-width: 760px) 100vw, 50vw')}<span>North Wales · Dining room</span><h3>Classic trim, restrained color.</h3></article><article>{picture('den','Finished North Wales den by Cascade Painting',1,'','lazy',None,'(max-width: 760px) 100vw, 50vw')}<span>North Wales · Den</span><h3>A softer palette for a lived-in room.</h3></article><article>{picture('deck','Finished exterior deck by Cascade Painting',1,'','lazy',None,'(max-width: 760px) 100vw, 50vw')}<span>Exterior · Deck finish</span><h3>Outdoor surfaces made cohesive again.</h3></article><article>{picture('garage','Finished garage with coated floor by Cascade Painting',1,'','lazy',None,'(max-width: 760px) 100vw, 50vw')}<span>Garage · Floor coating</span><h3>Utility space, treated like part of the home.</h3></article><article>{picture('basement','Finished basement coating project by Cascade Painting',1,'','lazy',None,'(max-width: 760px) 100vw, 50vw')}<span>Basement · Coating</span><h3>A brighter, cleaner working surface.</h3></article><article>{picture('maple-glen','Finished Maple Glen room by Cascade Painting',1,'','lazy',None,'(max-width: 760px) 100vw, 50vw')}<span>Maple Glen · Interior</span><h3>A quiet finish after the hard prep work.</h3></article></div></div></section>'''+inline_cta(1,'Have a space you want us to think through?')
write(Path('projects/index.html'),page_shell('Painting Projects in Montgomery County, PA | Cascade Painting','Explore real Cascade Painting interior, exterior, cabinet and coating projects completed around Montgomery County, Pennsylvania.','/projects/',1,projects_body,'Projects',image='living-room-wide-1600.webp'))

# Standard page
standard_body=page_hero('The Cascade Standard','The finish matters. So does everything that happens before it.','A professional painting project should feel organized, respectful and predictable from the first conversation through the final walkthrough.','dining-room','Finished dining room with crisp painted walls and trim by Cascade Painting',1)+'''
<section class="standard-page"><div class="wrap standard-page-grid"><article><span>01</span><h2>Understand the room.</h2><p>We start with the surfaces, the condition, the goals and the way the space needs to function while work is underway.</p></article><article><span>02</span><h2>Define the scope.</h2><p>Painting, repairs, prep, protection and exclusions are discussed before the project is treated like a schedule.</p></article><article><span>03</span><h2>Protect and prepare.</h2><p>Floors, furniture and adjacent surfaces are protected. Repairs and prep are completed before finish work begins.</p></article><article><span>04</span><h2>Communicate while we work.</h2><p>You should know what is happening, what comes next and who to contact without chasing the contractor for answers.</p></article><article><span>05</span><h2>Finish with discipline.</h2><p>Coverage, lines, edges and touch points are checked as the room comes together.</p></article><article><span>06</span><h2>Walk it together.</h2><p>The project closes with a walkthrough and attention to the final details, not a van disappearing as soon as the last coat dries.</p></article></div></section>'''+inline_cta()
write(Path('our-standard/index.html'),page_shell('The Cascade Standard | Cascade Painting','Learn how Cascade Painting approaches project scope, preparation, communication, finish work and final walkthroughs.','/our-standard/',1,standard_body,'Our Standard',image='dining-room-1600.webp'))

# About page
about_body=page_hero('About Cascade','A local painting company built around accountability, not volume.','Cascade Painting is veteran and family owned, based in Lansdale and focused on careful work, clear communication and long-term local relationships.','maple-glen','Finished local interior painting project by Cascade Painting',1)+f'''
<section class="content-section"><div class="wrap about-grid"><div><p class="eyebrow">Why Cascade exists</p><h2>Craftsmanship and a professional experience should come together.</h2><p class="lead-copy">Cascade Painting is veteran and family owned and based in Lansdale. The company was built around a simple idea: the finish matters, but so does the way a homeowner experiences the project.</p><p>That means clear scope before work starts, protection of the space, repairs handled before finish coats, straightforward communication while the work is underway and a deliberate walkthrough at the end. Staying owner-led and locally focused keeps accountability close to the project instead of buried behind layers of handoffs.</p><p>We serve homeowners and select businesses throughout Lansdale and nearby Montgomery County communities, including North Wales, Ambler, Blue Bell and Maple Glen.</p></div><div class="about-values"><div><strong>Veteran & family owned</strong><p>Service, accountability and pride in the work are part of the operating standard.</p></div><div><strong>Local to Montgomery County</strong><p>Based in Lansdale and built to serve nearby communities rather than chase a giant service radius.</p></div><div><strong>Preparation-driven</strong><p>Drywall repair, wallpaper removal and surface correction are treated as part of finish quality, not separate from it.</p></div><div><strong>Direct communication</strong><p>The goal is fewer handoffs, fewer surprises and a clear point of contact.</p></div></div></div></section>'''+inline_cta()
write(Path('about/index.html'),page_shell('About Cascade Painting | Lansdale, PA','Learn about Cascade Painting, a veteran and family-owned painting company based in Lansdale and serving Montgomery County, PA.','/about/',1,about_body,'About',image='maple-glen-1600.webp'))

# Reviews page
reviews_body=page_hero('Customer feedback','The most useful proof is what people say after they have lived through the project.','Read public Google reviews from Cascade Painting clients and learn what they noticed about the work, communication and jobsite experience.','living-room-alt','Finished interior painting project by Cascade Painting',1)+f'''<section class="review-page" data-google-reviews data-review-limit="12"><div class="wrap review-page-intro"><div><p class="eyebrow">Google reviews</p><h2>Public feedback, straight from the source.</h2></div><p>Recent reviews come directly from our Google Business Profile. Read the feedback below or open the full public listing on Google.</p></div><div class="wrap google-review-card light"><div><span>Google Business Profile</span><strong data-review-summary>Read customer feedback on Google.</strong><p data-review-summary-detail>See current reviews for Cascade Painting on the public listing.</p></div><a class="btn btn-primary" data-review-link href="{SITE['google_maps']}" target="_blank" rel="noopener noreferrer">Open Google Reviews ↗</a></div>{google_reviews_feed()}<div class="wrap review-actions"><a class="btn btn-ghost" href="../estimate/">Request an Estimate</a></div></section>'''+inline_cta()
write(Path('reviews/index.html'),page_shell('Cascade Painting Reviews | Lansdale, PA','Read public Google reviews and customer feedback for Cascade Painting in Lansdale and Montgomery County, Pennsylvania.','/reviews/',1,reviews_body,'Reviews',image='living-room-alt-1600.webp'))

# Service area overview
areas=[('Lansdale','painting-contractor-lansdale-pa/','Home base · Full service'),('North Wales','service-areas/north-wales-pa/','Featured interior work'),('Ambler','service-areas/ambler-pa/','Residential painting'),('Blue Bell','service-areas/blue-bell-pa/','Residential painting'),('Maple Glen','service-areas/maple-glen-pa/','Featured interior work'),('Horsham','','Interior · exterior'),('Plymouth Meeting','','Interior · exterior'),('Willow Grove','','Interior · exterior'),('Chalfont','','Interior · exterior'),('Montgomeryville','','Interior · exterior')]
area_cards=''.join(f'<a class="area-card" href="{("../"+href) if href else "../estimate/"}"><span>{i:02d}</span><strong>{name}</strong><small>{sub}</small><b>↗</b></a>' for i,(name,href,sub) in enumerate(areas,1))
areas_body=page_hero('Service area','Local by design.','Cascade Painting is based in Lansdale and serves nearby communities throughout Montgomery County and the surrounding area.','deck','Exterior project completed by Cascade Painting in the Montgomery County area',1)+f'''<section class="area-page"><div class="wrap"><div class="section-title-row"><div><p class="eyebrow">Where we work</p><h2>A tighter service area keeps the service personal.</h2></div><p>We prioritize the communities around our Lansdale home base so estimating, scheduling and follow-through stay practical.</p></div><div class="area-page-grid">{area_cards}</div></div></section>'''+inline_cta()
write(Path('service-areas/index.html'),page_shell('Painting Service Areas | Cascade Painting, Lansdale PA','Cascade Painting serves Lansdale, North Wales, Ambler, Blue Bell, Maple Glen and surrounding Montgomery County communities.','/service-areas/',1,areas_body,'Service Areas',image='deck-1600.webp'))

# Location pages
locations=[
 {
  'slug':'painting-contractor-lansdale-pa','city':'Lansdale','h1':'Lansdale painter with a local point of accountability.','lead':'Based at 24 Green St, Cascade Painting provides interior, exterior, cabinet, repair and coating services for homeowners and select businesses in Lansdale and nearby communities.','img':'kitchen',
  'intro':'Being based in Lansdale makes this more than a keyword on a service-area page. It is the center of the area we work in. Projects can range from a single room or drywall repair to whole-interior repainting, exterior work, cabinet refinishing and garage or basement coatings.',
  'planning':'For a useful estimate, we look at the condition of the surfaces, the amount of repair and preparation required, access, occupied-space protection, finish expectations and the sequence of the work. That keeps the scope tied to the actual project instead of a generic per-room number.',
  'proof':'From Lansdale we regularly work into North Wales, Montgomeryville, Ambler, Blue Bell, Maple Glen, Horsham and other nearby communities.'
 },
 {
  'slug':'service-areas/north-wales-pa','city':'North Wales','h1':'Painting in North Wales backed by real local project work.','lead':'Cascade has completed multi-room interior, drywall repair and finish work in North Wales, giving prospective clients nearby project proof instead of a generic location page.','img':'living-room-wide',
  'intro':'North Wales is one of the communities where our current portfolio already includes real interior work. Those projects show the kind of details we care about: repaired surfaces, clean transitions, ceilings and trim handled as part of the room, and a finish that works with the existing architecture and natural light.',
  'planning':'Interior projects often expand once the surfaces are inspected closely. Patches, openings, previous repairs, wallpaper residue or trim transitions may need attention before paint. We define that prep in the scope so the finish is not being asked to hide a surface problem.',
  'proof':'See the project journal for finished North Wales living, dining and den spaces photographed after Cascade Painting completed the work.'
 },
 {
  'slug':'service-areas/ambler-pa','city':'Ambler','h1':'Interior and exterior painting for Ambler homes.','lead':'Cascade Painting serves Ambler homeowners with preparation-first interior and exterior painting, cabinet refinishing, drywall repair and related finish work.','img':'dining-room',
  'intro':'A painting project in Ambler can be as focused as a room refresh or as involved as multiple interior spaces, exterior surfaces, cabinets or repair work. Our approach starts with the actual condition of the home and the surfaces rather than forcing every project into the same package.',
  'planning':'We pay particular attention to protection, repair scope, sheen transitions, trim and edges because those are the details homeowners keep seeing after the ladders are gone. The estimate should make those expectations visible before work begins.',
  'proof':'Ambler is within Cascade Painting’s core Montgomery County service area from our Lansdale base.'
 },
 {
  'slug':'service-areas/blue-bell-pa','city':'Blue Bell','h1':'Detail-driven painting for Blue Bell homes.','lead':'Interior, exterior, cabinet and surface-preparation services for Blue Bell homeowners who want clear scope, careful execution and direct communication.','img':'den',
  'intro':'For Blue Bell projects, the goal is not simply to put new color on the walls. We look at how the existing finishes, trim, ceilings, repairs and adjoining surfaces come together so the completed space feels intentional rather than pieced together.',
  'planning':'Before scheduling the work, we define what is included, what needs repair, what will be protected and what finish system is appropriate. That preparation is especially important in occupied homes where cleanliness and sequence affect the experience as much as the final coat.',
  'proof':'Blue Bell is part of our regular Montgomery County service area, with estimating and project planning handled from nearby Lansdale.'
 },
 {
  'slug':'service-areas/maple-glen-pa','city':'Maple Glen','h1':'Painting in Maple Glen with local project proof.','lead':'Cascade Painting serves Maple Glen with interior painting, wallpaper removal, drywall repair, exterior painting and related finish work.','img':'maple-glen',
  'intro':'Our Maple Glen portfolio includes finished interior work that reflects the part of painting we emphasize most: what happens before the finish coat. Wallpaper removal, wall preparation, repair and clean trim transitions can determine whether a room reads as truly finished.',
  'planning':'When wallpaper or damaged surfaces are involved, the condition underneath is evaluated after removal. Cleaning, repair, sanding and priming are handled as needed before the new finish is applied. That process is defined in the scope rather than treated as an afterthought.',
  'proof':'The Maple Glen project photography on this site is real Cascade Painting work, not stock imagery.'
 }
]
for item in locations:
    slug,city,h1,lead,img=item['slug'],item['city'],item['h1'],item['lead'],item['img']
    depth=1 if '/' not in slug else 2
    path='/'+slug+'/'
    body=page_hero(f'Painting contractor · {city}, PA',h1,lead,img,f'Cascade Painting project serving {city}, Pennsylvania',depth)+f'''<section class="content-section location-detail"><div class="wrap location-content"><div><p class="eyebrow">Local service</p><h2>What Cascade brings to a {city} project.</h2><p class="lead-copy">{item['intro']}</p><p>{item['planning']}</p><p class="local-proof-note">{item['proof']}</p></div><div><div class="location-services"><a href="{rel(depth,'interior-painting-lansdale-pa/')}">Interior painting <span>↗</span></a><a href="{rel(depth,'exterior-painting-lansdale-pa/')}">Exterior painting <span>↗</span></a><a href="{rel(depth,'cabinet-refinishing-lansdale-pa/')}">Cabinet refinishing <span>↗</span></a><a href="{rel(depth,'wallpaper-removal-drywall-repair/')}">Drywall & surface repair <span>↗</span></a><a href="{rel(depth,'floor-coatings-lansdale-pa/')}">Floor coatings <span>↗</span></a></div><div class="location-expect"><p class="eyebrow">What to expect</p><ul><li>Scope tied to the actual surfaces</li><li>Protection and preparation defined up front</li><li>Clear point of contact during the project</li><li>Final walkthrough before closeout</li></ul></div></div></div></section>'''+inline_cta(depth,f'Planning a project in {city}?')
    desc=f'Cascade Painting provides interior, exterior, cabinet, drywall repair and coating services in {city}, PA and nearby Montgomery County communities.'
    schema=service_schema(f'Painting services in {city}, Pennsylvania',desc,SITE['domain']+path)
    bread=breadcrumbs_schema([('Home',SITE['domain']+'/'),('Service Areas',SITE['domain']+'/service-areas/'),(city,SITE['domain']+path)])
    write(Path(slug)/'index.html',page_shell(f'Painter in {city}, PA | Cascade Painting',desc,path,depth,body,'Service Areas',image=f'{img}-{manifest[img][-1]["width"]}.webp',schema=schema,extra_schema=bread,preload=manifest[img][-1]['file']))

# Estimate page
estimate_body=f'''<section class="estimate-hero"><div class="wrap estimate-grid"><div class="estimate-copy"><p class="eyebrow">Start a project</p><h1>Tell us what you want to change.</h1><p>Share enough for us to understand the project. We use these details to confirm fit and make the next conversation more useful.</p><div class="estimate-assurance"><div><strong>1. Share the basics</strong><span>Service, location, timing and project details.</span></div><div><strong>2. We review the scope</strong><span>We follow up to clarify the surfaces, goals and next step.</span></div><div><strong>3. On-site when needed</strong><span>Projects that need a closer look can be scheduled for an in-person estimate.</span></div></div><div class="estimate-contact"><a href="tel:{SITE['phone_href']}"><span>Prefer to call?</span><strong>{SITE['phone']}</strong></a><a href="mailto:{SITE['email']}"><span>Prefer email?</span><strong>{SITE['email']}</strong></a></div><p class="privacy-note">Your project details are used to respond to your inquiry. <a href="../privacy/">Privacy policy</a>.</p></div><form class="estimate-form" data-estimate-form novalidate><div class="form-progress" aria-label="Estimate request progress"><span class="is-active" data-step-dot="1">1</span><i></i><span data-step-dot="2">2</span><i></i><span data-step-dot="3">3</span></div><section class="form-step is-active" data-step="1"><p class="form-kicker">Step 1 of 3</p><h2>What are we looking at?</h2><div class="choice-grid"><label><input type="radio" name="projectType" value="Interior Painting" required><span>Interior Painting</span></label><label><input type="radio" name="projectType" value="Exterior Painting"><span>Exterior Painting</span></label><label><input type="radio" name="projectType" value="Cabinet Refinishing"><span>Cabinet Refinishing</span></label><label><input type="radio" name="projectType" value="Drywall / Wallpaper"><span>Drywall / Wallpaper</span></label><label><input type="radio" name="projectType" value="Floor Coating"><span>Floor Coating</span></label><label><input type="radio" name="projectType" value="Commercial"><span>Commercial</span></label></div><div class="form-nav"><span></span><button class="btn btn-primary" type="button" data-next>Continue →</button></div></section><section class="form-step" data-step="2"><p class="form-kicker">Step 2 of 3</p><h2>Give us the project context.</h2><div class="field-grid"><label><span>City / ZIP</span><input name="location" autocomplete="postal-code" required maxlength="80" placeholder="Lansdale, 19446"></label><label><span>Ideal timing</span><select name="timing" required><option value="">Select</option><option>As soon as practical</option><option>Within 1 month</option><option>1–3 months</option><option>3+ months</option><option>Just planning</option></select></label><label class="full"><span>Project details</span><textarea name="details" required maxlength="5000" placeholder="Rooms, surfaces, repairs, colors, access, goals — whatever helps us understand the scope."></textarea></label><label class="honeypot" aria-hidden="true"><span>Website</span><input name="website" tabindex="-1" autocomplete="off"></label></div><div class="form-nav"><button class="btn btn-ghost" type="button" data-back>← Back</button><button class="btn btn-primary" type="button" data-next>Continue →</button></div></section><section class="form-step" data-step="3"><p class="form-kicker">Step 3 of 3</p><h2>How should we reach you?</h2><div class="field-grid"><label><span>Name</span><input name="name" autocomplete="name" required maxlength="140"></label><label><span>Phone</span><input name="phone" type="tel" inputmode="tel" autocomplete="tel" required maxlength="40"></label><label class="full"><span>Email</span><input name="email" type="email" inputmode="email" autocomplete="email" required maxlength="180"></label></div><label class="consent"><input type="checkbox" required name="consent"><span>I am asking Cascade Painting to contact me about this project.</span></label><div class="form-nav"><button class="btn btn-ghost" type="button" data-back>← Back</button><button class="btn btn-primary" type="submit">Send Project Details ↗</button></div><p class="form-status" data-form-status aria-live="polite"></p></section><div class="form-success" data-form-success hidden><p class="eyebrow">Request received</p><h2>Thanks. We have your project details.</h2><p>We will review what you sent and follow up using the contact information you provided.</p><a class="btn btn-ghost" href="../projects/">View recent work</a></div><noscript><p class="noscript-form">JavaScript is required for the project form. You can also call <a href="tel:{SITE['phone_href']}">{SITE['phone']}</a> or email <a href="mailto:{SITE['email']}">{SITE['email']}</a>.</p></noscript></form></div></section>'''
write(Path('estimate/index.html'),page_shell('Request a Painting Estimate | Cascade Painting','Request a painting estimate from Cascade Painting for interior, exterior, cabinet, drywall, coating or commercial work in Montgomery County, PA.','/estimate/',1,estimate_body))

# Privacy
privacy_body='''<section class="legal-page"><div class="wrap narrow"><p class="eyebrow">Privacy</p><h1>Privacy policy.</h1><p>When you submit a project inquiry, Cascade Painting uses the information you provide to respond to your request, prepare an estimate and communicate about the project. We do not sell inquiry information.</p><h2>Information collected</h2><p>The estimate form may collect your name, email, phone number, project location, service type, timing and project details. Standard server logs may also record technical information such as IP address, browser and request timing for security and reliability.</p><h2>Third-party services</h2><p>The website is hosted through Cloudflare and may use third-party services for email delivery, spam prevention or future analytics. The reviews section displays public Google Business Profile data. Reviewer profile photos, when available, load from Google, and links to the public listing are processed under Google’s policies.</p><h2>Contact</h2><p>Questions about this policy can be sent to <a href="mailto:paxton@cascadepaintingpa.com">paxton@cascadepaintingpa.com</a>.</p><p class="muted">Last updated September 2026.</p></div></section>'''
write(Path('privacy/index.html'),page_shell('Privacy Policy | Cascade Painting','Privacy policy for Cascade Painting website inquiries.','/privacy/',1,privacy_body,indexable=False))

# 404
notfound=f'''<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><meta name="theme-color" content="#143746"><title>Page Not Found | Cascade Painting</title><link rel="icon" href="/images/favicon.png" sizes="96x96" type="image/png"><link rel="stylesheet" href="/assets/site.css"></head><body><main class="notfound"><div><img src="/images/logo.png" width="488" height="289" alt="Cascade Painting"><p class="eyebrow">404</p><h1>That page moved on.</h1><p>Use the homepage to keep browsing or tell us about the project you have in mind.</p><div class="hero-actions"><a class="btn btn-primary" href="/">Home</a><a class="btn btn-ghost" href="/estimate/">Request an Estimate</a></div></div></main></body></html>'''
write(Path('404.html'),notfound)

# SEO/support files
indexable_urls=['/','/services/','/interior-painting-lansdale-pa/','/exterior-painting-lansdale-pa/','/cabinet-refinishing-lansdale-pa/','/commercial-painting-lansdale-pa/','/floor-coatings-lansdale-pa/','/wallpaper-removal-drywall-repair/','/projects/','/our-standard/','/about/','/reviews/','/service-areas/','/painting-contractor-lansdale-pa/','/service-areas/north-wales-pa/','/service-areas/ambler-pa/','/service-areas/blue-bell-pa/','/service-areas/maple-glen-pa/','/estimate/']
lastmod='2026-09-15'
sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{SITE["domain"]}{u}</loc><lastmod>{lastmod}</lastmod></url>\n' for u in indexable_urls)+'</urlset>'
write(Path('sitemap.xml'),sitemap)

# Build the image sitemap from images actually embedded on each indexable landing page.
def html_path_for_url(url):
    return PUBLIC/'index.html' if url == '/' else PUBLIC/url.strip('/')/'index.html'

image_sitemap_rows=[]
for url in indexable_urls:
    page_path=html_path_for_url(url)
    if not page_path.exists():
        continue
    page_text=page_path.read_text(encoding='utf-8')
    page_images=[]
    for src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', page_text, flags=re.I):
        if '/images/' not in src and not src.startswith('images/') and not src.startswith('../images/'):
            continue
        filename=src.split('/images/')[-1] if '/images/' in src else src.split('images/')[-1]
        filename=filename.split('?')[0]
        if filename in {'logo.png','favicon.png','apple-touch-icon.png','favicon-512.png'}:
            continue
        absolute=f'{SITE["domain"]}/images/{filename}'
        if absolute not in page_images:
            page_images.append(absolute)
    if page_images:
        image_sitemap_rows.append('<url><loc>'+SITE['domain']+url+'</loc>'+''.join(f'<image:image><image:loc>{img}</image:loc></image:image>' for img in page_images)+'</url>')
img_sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'+'\n'.join(image_sitemap_rows)+'\n</urlset>'
write(Path('image-sitemap.xml'),img_sitemap)

write(Path('robots.txt'),f'''User-agent: *
Allow: /
Disallow: /api/

Sitemap: {SITE['domain']}/sitemap.xml
Sitemap: {SITE['domain']}/image-sitemap.xml
''')
write(Path('llms.txt'),f'''# Cascade Painting

Cascade Painting is a veteran and family-owned painting company based in Lansdale, Pennsylvania, serving Montgomery County and nearby communities.

Primary services:
- Interior painting
- Exterior painting
- Cabinet refinishing
- Drywall repair and wallpaper removal
- Garage and basement floor coatings
- Commercial painting and select line striping

Primary areas served:
- Lansdale, PA
- North Wales, PA
- Ambler, PA
- Blue Bell, PA
- Maple Glen, PA
- Horsham, PA
- Plymouth Meeting, PA
- Willow Grove, PA

Contact:
- Phone: {SITE['phone']}
- Email: {SITE['email']}
- Website: {SITE['domain']}

Canonical service and location information should be taken from the website pages and sitemap.
''')
write(Path('site.webmanifest'),json.dumps({'id':'/','name':'Cascade Painting','short_name':'Cascade Painting','start_url':'/','scope':'/','display':'standalone','background_color':'#f5f1e8','theme_color':'#143746','icons':[{'src':'/images/favicon-512.png','sizes':'512x512','type':'image/png'},{'src':'/images/apple-touch-icon.png','sizes':'180x180','type':'image/png'}]},indent=2))

write(Path('_redirects'),'''/interior-painting /interior-painting-lansdale-pa/ 301
/interior-painting/ /interior-painting-lansdale-pa/ 301
/exterior-painting /exterior-painting-lansdale-pa/ 301
/exterior-painting/ /exterior-painting-lansdale-pa/ 301
/cabinet-painting /cabinet-refinishing-lansdale-pa/ 301
/cabinet-painting/ /cabinet-refinishing-lansdale-pa/ 301
/cabinet-painting-lansdale-pa /cabinet-refinishing-lansdale-pa/ 301
/cabinet-painting-lansdale-pa/ /cabinet-refinishing-lansdale-pa/ 301
/commercial-painting /commercial-painting-lansdale-pa/ 301
/commercial-painting/ /commercial-painting-lansdale-pa/ 301
/epoxy-flooring /floor-coatings-lansdale-pa/ 301
/epoxy-flooring/ /floor-coatings-lansdale-pa/ 301
/lansdale-pa /painting-contractor-lansdale-pa/ 301
/lansdale-pa/ /painting-contractor-lansdale-pa/ 301
/google-reviews /reviews/ 301
/google-reviews/ /reviews/ 301
/quote /estimate/ 301
/quote/ /estimate/ 301
/contact /estimate/ 301
/contact/ /estimate/ 301
''')

# Static filenames are intentionally not cached forever because CSS/JS keep stable names.
write(Path('_headers'),'''/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Frame-Options: SAMEORIGIN
  Cross-Origin-Opener-Policy: same-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains

/assets/*
  Cache-Control: public, max-age=3600, stale-while-revalidate=86400

/images/*
  Cache-Control: public, max-age=2592000, stale-while-revalidate=604800
''')
print('built indexable pages',len(indexable_urls))


# V4 enhancement hook
from v4_enhancements import apply as apply_v4_enhancements
apply_v4_enhancements()
