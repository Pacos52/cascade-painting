from pathlib import Path
import json, re, html
from datetime import date

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'public'
MANIFEST = json.loads((PUBLIC / 'images' / 'image-manifest.json').read_text(encoding='utf-8'))
DOMAIN = 'https://cascadepaintingpa.com'
PHONE = '267-461-4367'
PHONE_HREF = '+12674614367'
EMAIL = 'paxton@cascadepaintingpa.com'
ADDRESS = '24 Green St, Lansdale, PA 19446'
GOOGLE_MAPS = 'https://www.google.com/maps/search/?api=1&query=Cascade+Painting'
ASSET_VERSION = 'v4-2-20260923'
TODAY = '2026-09-16'


def variants(name):
    return MANIFEST[name]


def img(name, alt, cls='', loading='lazy', fetchpriority=None, sizes='(max-width: 760px) 100vw, 50vw'):
    vs = variants(name)
    largest = vs[-1]
    srcset = ', '.join(f"/images/{v['file']} {v['width']}w" for v in vs)
    attrs = [
        f'alt="{html.escape(alt, quote=True)}"',
        f'width="{largest["width"]}"',
        f'height="{largest["height"]}"',
        f'src="/images/{largest["file"]}"',
        f'srcset="{srcset}"',
        f'sizes="{sizes}"',
        'decoding="async"'
    ]
    if cls:
        attrs.insert(0, f'class="{cls}"')
    if loading:
        attrs.append(f'loading="{loading}"')
    if fetchpriority:
        attrs.append(f'fetchpriority="{fetchpriority}"')
    return '<img ' + ' '.join(attrs) + '>'


def schema_graph(title, desc, path, image_name, article=False, article_type='Article'):
    canonical = DOMAIN + path
    largest = variants(image_name)[-1]['file']
    graph = [
        {
            '@type': ['HomeAndConstructionBusiness', 'HousePainter'],
            '@id': DOMAIN + '/#business',
            'name': 'Cascade Painting',
            'url': DOMAIN + '/',
            'logo': DOMAIN + '/images/logo.png',
            'image': DOMAIN + '/images/hero-kitchen-1600.webp',
            'telephone': '+1-267-461-4367',
            'email': EMAIL,
            'description': 'Veteran and family-owned painting company based in Lansdale and serving Montgomery County, Pennsylvania.',
            'slogan': 'Not your typical contractor experience.',
            'address': {
                '@type': 'PostalAddress', 'streetAddress': '24 Green St', 'addressLocality': 'Lansdale',
                'addressRegion': 'PA', 'postalCode': '19446', 'addressCountry': 'US'
            },
            'areaServed': [{'@type':'City','name':x} for x in ['Lansdale, PA','North Wales, PA','Ambler, PA','Blue Bell, PA','Maple Glen, PA','Horsham, PA','Plymouth Meeting, PA','Willow Grove, PA']],
            'contactPoint': {'@type':'ContactPoint','telephone':'+1-267-461-4367','email':EMAIL,'contactType':'customer service','availableLanguage':'English'}
        },
        {'@type':'WebSite','@id':DOMAIN+'/#website','url':DOMAIN+'/','name':'Cascade Painting','publisher':{'@id':DOMAIN+'/#business'},'inLanguage':'en-US'},
        {'@type':'WebPage','@id':canonical+'#webpage','url':canonical,'name':title,'description':desc,'isPartOf':{'@id':DOMAIN+'/#website'},'about':{'@id':DOMAIN+'/#business'},'primaryImageOfPage':{'@type':'ImageObject','url':DOMAIN+'/images/'+largest},'inLanguage':'en-US'}
    ]
    if article:
        graph.append({
            '@type': article_type,
            '@id': canonical + '#article',
            'headline': title.split('|')[0].strip(),
            'description': desc,
            'mainEntityOfPage': {'@id':canonical+'#webpage'},
            'image': DOMAIN + '/images/' + largest,
            'author': {'@id':DOMAIN+'/#business'},
            'publisher': {'@id':DOMAIN+'/#business'},
            'datePublished': TODAY,
            'dateModified': TODAY,
            'inLanguage':'en-US'
        })
    return {'@context':'https://schema.org','@graph':graph}


def breadcrumb_schema(items):
    return {'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[
        {'@type':'ListItem','position':i+1,'name':name,'item':url} for i,(name,url) in enumerate(items)
    ]}


def head(title, desc, path, image_name, article=False, extra_schema=None, preload=False):
    canonical = DOMAIN + path
    image_file = variants(image_name)[-1]['file']
    social_file = f'og-{image_name}.jpg' if (PUBLIC/'images'/f'og-{image_name}.jpg').exists() else 'og-cascade.jpg'
    preload_html = ''
    if preload:
        vs = variants(image_name)
        srcset = ', '.join(f"/images/{v['file']} {v['width']}w" for v in vs)
        preload_html = f'<link rel="preload" as="image" href="/images/{image_file}" imagesrcset="{srcset}" imagesizes="100vw" fetchpriority="high">'
    schemas = [schema_graph(title, desc, path, image_name, article)]
    if extra_schema:
        schemas.append(extra_schema)
    schema_html = ''.join(f'<script type="application/ld+json">{json.dumps(s,separators=(",",":"))}</script>' for s in schemas)
    return f'''<!doctype html><html lang="en-US"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc,quote=True)}"><meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"><link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#143746"><meta name="color-scheme" content="light"><meta name="format-detection" content="telephone=no"><meta name="author" content="Cascade Painting">
<meta property="og:type" content="{'article' if article else 'website'}"><meta property="og:locale" content="en_US"><meta property="og:site_name" content="Cascade Painting"><meta property="og:title" content="{html.escape(title,quote=True)}"><meta property="og:description" content="{html.escape(desc,quote=True)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{DOMAIN}/images/{social_file}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:type" content="image/jpeg">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{html.escape(title,quote=True)}"><meta name="twitter:description" content="{html.escape(desc,quote=True)}"><meta name="twitter:image" content="{DOMAIN}/images/{social_file}">
<link rel="icon" href="/images/favicon.png" sizes="96x96" type="image/png"><link rel="apple-touch-icon" href="/images/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">{preload_html}<link rel="stylesheet" href="/assets/site.css?v={ASSET_VERSION}">{schema_html}</head>'''


def header(active=''):
    links=[('Services','/services/'),('Projects','/projects/'),('Our Standard','/our-standard/'),('About','/about/'),('Service Areas','/service-areas/'),('Reviews','/reviews/')]
    nav=''.join(f'<a {"aria-current=\"page\"" if label==active else ""} href="{href}">{label}</a>' for label,href in links)
    return f'''<body><a class="skip-link" href="#main">Skip to content</a><div class="topline"><div class="wrap topline-inner"><span>Veteran & family owned · Montgomery County, PA</span><span>Interior · Exterior · Cabinets · Coatings</span></div></div><header class="site-header" data-header><div class="wrap header-inner"><a class="brand" href="/" aria-label="Cascade Painting home"><img src="/images/logo.png" width="488" height="289" alt="Cascade Painting" decoding="async"></a><nav class="desktop-nav" aria-label="Primary">{nav}</nav><div class="header-actions"><a class="phone-link" href="tel:{PHONE_HREF}">{PHONE}</a><a class="btn btn-primary btn-small" href="/estimate/">Request an Estimate</a><button class="menu-toggle" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-menu" data-menu-toggle><span></span><span></span></button></div></div></header><div class="mobile-menu" id="mobile-menu" data-mobile-menu aria-hidden="true"><nav aria-label="Mobile primary">{nav}</nav><div class="mobile-menu-actions"><a href="tel:{PHONE_HREF}" class="btn btn-ghost">Call {PHONE}</a><a href="/estimate/" class="btn btn-primary">Request an Estimate</a></div></div>'''


def footer():
    return f'''<footer class="site-footer"><div class="wrap footer-grid"><div class="footer-brand"><img src="/images/logo-footer.png" width="488" height="289" alt="Cascade Painting" loading="lazy" decoding="async"><p>Veteran and family-owned painting company based in Lansdale and serving communities throughout Montgomery County, Pennsylvania.</p><a class="text-link light-link" href="/estimate/">Start a project →</a></div><div class="footer-col"><span>Services</span><a href="/interior-painting-lansdale-pa/">Interior Painting</a><a href="/exterior-painting-lansdale-pa/">Exterior Painting</a><a href="/cabinet-refinishing-lansdale-pa/">Cabinet Refinishing</a><a href="/wallpaper-removal-drywall-repair/">Drywall & Wallpaper</a><a href="/floor-coatings-lansdale-pa/">Floor Coatings</a><a href="/commercial-painting-lansdale-pa/">Commercial Painting</a></div><div class="footer-col"><span>Company</span><a href="/projects/">Projects</a><a href="/our-standard/">Our Standard</a><a href="/about/">About</a><a href="/reviews/">Reviews</a><a href="/service-areas/">Service Areas</a><a href="/resources/">Resources</a></div><div class="footer-col"><span>Contact</span><a href="tel:{PHONE_HREF}">{PHONE}</a><a href="mailto:{EMAIL}">{EMAIL}</a><a href="{GOOGLE_MAPS}" target="_blank" rel="noopener noreferrer">{ADDRESS}</a><p>Mon–Fri 7 AM–7 PM<br>Sat 9 AM–5 PM</p></div></div><div class="wrap footer-bottom"><span>© <span data-year></span> Cascade Painting</span><div><a href="/privacy/">Privacy</a></div></div></footer><div class="mobile-cta" aria-label="Quick contact"><a href="tel:{PHONE_HREF}">Call</a><a href="/estimate/">Request Estimate</a></div><script src="/assets/site.js?v={ASSET_VERSION}" defer></script></body></html>'''


def shell(title, desc, path, body, image_name, active='', article=False, extra_schema=None, preload=False):
    return head(title, desc, path, image_name, article, extra_schema, preload) + header(active) + f'<main id="main">{body}</main>' + footer()


def breadcrumb_html(items):
    return '<nav class="breadcrumbs wrap" aria-label="Breadcrumb">' + '<span aria-hidden="true">Home</span>' + ''.join(f'<a href="{href}">{html.escape(name)}</a>' for name,href in items) + '</nav>'


def article_hero(kicker, title, lead, image_name, alt):
    return f'''<section class="article-hero"><div class="wrap article-hero-grid"><div><p class="eyebrow">{kicker}</p><h1>{title}</h1><p class="article-lead">{lead}</p><div class="article-meta"><span>By Cascade Painting</span><span>Updated September 2026</span><span>Montgomery County, PA</span></div></div><div class="article-hero-media">{img(image_name,alt,'','eager','high','(max-width: 980px) 100vw, 48vw')}</div></div></section>'''


RESOURCES = [
    {
        'slug':'interior-painting-preparation-guide',
        'title':'How to Prepare for Interior Painting | Cascade Painting',
        'h1':'How to prepare your home for an interior painting project.',
        'desc':'A practical homeowner guide to preparing rooms, furniture, walls, trim and expectations before an interior painting project in Montgomery County, PA.',
        'image':'living-room-wide',
        'lead':'The best interior projects start before the first finish coat. A little planning makes protection, repairs, access and daily cleanup much easier to manage.',
        'sections':[
            ('Decide what is actually part of the project','List the rooms and surfaces you want addressed: walls, ceilings, trim, doors, closets and built-ins. If you already know there are nail holes, drywall damage, failing caulk or wallpaper, identify those items early so the estimate can include the preparation rather than treating it as a surprise once work begins.'),
            ('Make access easy without emptying the whole house','Small furniture, fragile objects, wall art and electronics are usually easiest to move before work begins. Larger pieces can often remain in the room and be repositioned or protected depending on the scope. Clear pathways matter as much as clear walls because ladders, tools and materials need predictable access.'),
            ('Talk about repairs before choosing sheen','Paint does not hide surface problems; sheen can make them more visible. Glossier finishes reflect more light and can emphasize patches, texture differences and uneven walls. Repair expectations and surface condition should be part of the conversation before the final finish is selected.'),
            ('Plan around how the home is used','Pets, children, home offices, bedrooms and kitchens all change the sequence of a project. A useful schedule is not only about how quickly rooms can be painted. It should also account for where the household needs access and how each space can be returned to normal in a controlled way.'),
            ('Confirm the closeout plan','A project should end with the same clarity it started with. Confirm what will be reinstalled, what touch-ups are included, how leftover paint is handled and when the final walkthrough happens. Those small details are part of a professional experience, not an afterthought.')
        ],
        'service':'/interior-painting-lansdale-pa/','service_label':'Interior painting'
    },
    {
        'slug':'cabinet-refinishing-vs-replacement',
        'title':'Cabinet Refinishing vs. Replacement | Cascade Painting',
        'h1':'Cabinet refinishing or replacement: which project are you actually planning?',
        'desc':'Understand when cabinet refinishing can make sense, when replacement may be better, and what homeowners should evaluate before updating a kitchen.',
        'image':'cabinets',
        'lead':'If the cabinet layout works and the boxes and doors are in good condition, refinishing can change the room dramatically without rebuilding the kitchen. But it is not the right answer for every cabinet system.',
        'sections':[
            ('Start with the cabinet condition','Refinishing works best when the cabinet boxes, doors and drawer fronts are structurally sound. Swelling, failing veneers, broken joinery or a layout that simply does not work may point toward repair or replacement rather than a finish-only solution.'),
            ('Separate a color problem from a layout problem','If you like where everything is but dislike the finish, refinishing may address the real issue. If storage, appliance placement or traffic flow are the problems, a new color will not solve them. Decide which problem you are trying to fix before comparing project costs.'),
            ('The preparation is the project','Cabinet surfaces collect oils, cooking residue and years of handling. Degreasing, sanding or deglossing, repair, priming and a controlled finish system are what make cabinet work different from rolling a wall. The coating is only one part of the result.'),
            ('Think about hardware and surrounding finishes together','New cabinet color changes how counters, backsplash, flooring, walls and hardware read. A successful refresh often comes from treating those relationships as one design decision rather than selecting a cabinet color in isolation.'),
            ('Ask how doors and hardware will be managed','Organization matters. Doors, drawers and hardware need a system for removal, labeling, finishing and reassembly. The best process is the one that protects the finish and gets every component back where it belongs.')
        ],
        'service':'/cabinet-refinishing-lansdale-pa/','service_label':'Cabinet refinishing'
    },
    {
        'slug':'choosing-paint-sheen',
        'title':'How to Choose Paint Sheen for Your Home | Cascade Painting',
        'h1':'Choosing paint sheen without overthinking it.',
        'desc':'A practical guide to choosing flat, matte, eggshell, satin and higher-sheen finishes for walls, ceilings, trim and high-use spaces.',
        'image':'dining-room',
        'lead':'Sheen affects appearance, washability and how much surface texture you notice. The right choice depends on the surface and how the room is used, not a single rule for the whole house.',
        'sections':[
            ('Ceilings usually benefit from lower reflection','Flat or very low-sheen ceiling finishes help keep attention on the room rather than highlighting every change in texture or light. Specialty spaces can be different, but low reflection is a useful default for most ceilings.'),
            ('Walls are a balance between appearance and cleanability','Lower sheens tend to look softer and hide more surface variation. Eggshell and satin finishes are often considered when more washability is useful, especially in busy spaces. Product performance varies, so the exact label on the can matters less than the behavior of the coating system being specified.'),
            ('Trim benefits from definition','Doors, baseboards, casing and other trim are commonly given more sheen than walls. The added contrast can help the details read cleanly and can make high-touch surfaces easier to maintain.'),
            ('Natural light changes everything','A finish that looks subtle in a north-facing room can feel much more reflective in a room with large windows or strong recessed lighting. Samples should be evaluated in the actual room and at different times of day.'),
            ('Surface condition still comes first','Higher sheen is less forgiving of repairs and texture changes. If a wall has extensive patches or unevenness, improving the surface may matter more than debating between two adjacent sheen levels.')
        ],
        'service':'/interior-painting-lansdale-pa/','service_label':'Interior painting'
    },
    {
        'slug':'exterior-painting-prep-pennsylvania',
        'title':'Exterior Painting Preparation in Pennsylvania | Cascade Painting',
        'h1':'What exterior painting preparation looks like in Pennsylvania.',
        'desc':'A homeowner guide to exterior paint preparation, weather, scraping, caulking, priming and coating decisions for Pennsylvania homes.',
        'image':'deck',
        'lead':'Exterior paint has to live through moisture, heat, cold and seasonal movement. The finish is only as reliable as the surface underneath it and the conditions when it is applied.',
        'sections':[
            ('Inspect before deciding how to prep','Peeling paint, chalking, failed caulk, bare substrate, staining and moisture symptoms do not all require the same response. Preparation should be based on what is failing and why, not a single checklist applied to every house.'),
            ('Cleaning is about adhesion, not appearance','Dirt, mildew, chalk and contamination can interfere with a coating system. Cleaning is meant to create a sound surface for the next steps, not just make siding look better for a day.'),
            ('Loose coating has to be addressed','New paint does not stabilize a failing layer underneath it. Scraping and sanding are used where needed to remove loose material and soften transitions so the new system is bonding to something sound.'),
            ('Bare or repaired areas may need primer','Spot priming or a broader primer application can be appropriate depending on the substrate, old coating and amount of exposed material. The product system should match the actual condition rather than being selected from habit.'),
            ('Weather windows matter','Temperature, surface temperature, rain, dew and humidity can all affect application and cure. Exterior scheduling in Pennsylvania has to leave room for changing conditions instead of treating every dry-looking day as identical.')
        ],
        'service':'/exterior-painting-lansdale-pa/','service_label':'Exterior painting'
    },
    {
        'slug':'wallpaper-removal-wall-prep',
        'title':'Wallpaper Removal and Wall Preparation | Cascade Painting',
        'h1':'What happens after wallpaper comes off matters just as much as removing it.',
        'desc':'Learn what homeowners should expect from wallpaper removal, adhesive cleanup, wall repair, sanding, priming and preparation before painting.',
        'image':'maple-glen',
        'lead':'Wallpaper removal is rarely just a stripping task. The wall underneath may need adhesive cleanup, patching, sanding and priming before it is truly ready for a painted finish.',
        'sections':[
            ('Removal reveals the real condition of the wall','Until the paper is off, it can be difficult to know whether the wall is clean drywall, previously painted plaster, damaged facing paper or a patchwork of older repairs. The post-removal condition should guide the next steps.'),
            ('Adhesive residue has to be dealt with','Remaining paste can interfere with paint and primer. Cleaning and testing the surface matters because residue that looks harmless can create adhesion or finish problems later.'),
            ('Repairs should disappear into the wall, not become new focal points','Gouges, torn facing paper, old seams and patched areas need to be stabilized and feathered. The goal is not simply to fill damage; it is to make the repaired area behave and look like the surrounding surface under paint.'),
            ('Primer can be part of the transition from wallpaper to paint','Depending on the wall condition, primer can help seal repaired areas, equalize porosity and create a consistent surface for the finish coats. The exact primer choice should match what is exposed after removal.'),
            ('Expect the scope to become clearer after removal','A responsible estimate can anticipate common repair needs, but hidden conditions are still hidden conditions. The process should allow for evaluating the wall once the paper is gone rather than pretending every removal project is identical.')
        ],
        'service':'/wallpaper-removal-drywall-repair/','service_label':'Wallpaper removal & drywall repair'
    }
]

PROJECTS = [
    {
        'slug':'north-wales-living-room-refresh','title':'North Wales Living Room Painting Project | Cascade Painting','h1':'A brighter North Wales living room built around light, not louder color.','desc':'Explore a real Cascade Painting living room project in North Wales, PA with walls, ceilings and finish work refreshed into a brighter neutral palette.','image':'living-room-wide','kicker':'North Wales, PA · Interior painting','lead':'This room already had strong architecture, skylights and dark flooring. The goal was to quiet the wall color so the light, fireplace and existing finishes could become the focus.','scope':['Walls and ceiling refresh','Trim and transition detailing','Surface preparation and touch-up repairs','Occupied-home protection and cleanup'],'gallery':['living-room-wide','living-room-alt','den'],
        'process':'The room had several strong visual elements competing with one another. Rather than adding another statement color, the project moved toward a restrained neutral finish that let the vaulted ceiling, skylights and whitewashed fireplace carry the space. The success of a change like this depends on keeping edges, ceiling transitions and repaired areas clean because lighter finishes make inconsistencies easier to notice.',
        'service':'/interior-painting-lansdale-pa/','service_label':'Interior painting'
    },
    {
        'slug':'north-wales-dining-room-refresh','title':'North Wales Dining Room Painting Project | Cascade Painting','h1':'A dining room refresh that kept the traditional details and simplified the palette.','desc':'Real Cascade Painting dining room work in North Wales, PA featuring crisp trim, light walls and a cleaner relationship with the existing hardwood and millwork.','image':'dining-room','kicker':'North Wales, PA · Interior painting','lead':'The room already had detailed trim and warm hardwood. The painting work was about making those permanent features read more clearly instead of competing with them.','scope':['Wall and trim painting','Careful work around existing millwork','Surface preparation before finish coats','Clean transitions at chair rail and crown'],'gallery':['dining-room','den','living-room-alt'],
        'process':'Traditional rooms can become visually busy when wall color, trim profiles, flooring and furnishings all ask for equal attention. A quieter wall finish creates separation and lets the millwork do its job. The technical part is making sure the chair rail, crown, corners and repaired surfaces stay crisp under strong room lighting.',
        'service':'/interior-painting-lansdale-pa/','service_label':'Interior painting'
    },
    {
        'slug':'garage-floor-coating-refresh','title':'Garage Painting and Floor Coating Project | Cascade Painting','h1':'Turning a garage into a space that feels finished instead of forgotten.','desc':'See a real Cascade Painting garage project with painted walls, trim and a finished concrete floor coating in Montgomery County, PA.','image':'garage','kicker':'Montgomery County · Garage & floor coating','lead':'Garages are utility spaces, but they do not have to look unfinished. This project paired a cleaner wall system with a coated concrete floor so the entire space read as one finished environment.','scope':['Concrete floor coating','Wall and trim painting','Surface cleaning and preparation','Detail work around shelving and garage hardware'],'gallery':['garage','garage-alt','basement'],
        'process':'Coating concrete starts with evaluating what is already on the slab and what may interfere with adhesion. Walls, base details and floor preparation have to be sequenced so one part of the project does not compromise another. The result is less about making a garage decorative and more about making it cleaner, brighter and easier to maintain.',
        'service':'/floor-coatings-lansdale-pa/','service_label':'Floor coatings'
    },
    {
        'slug':'basement-concrete-coating-refresh','title':'Basement Floor Coating Project | Cascade Painting','h1':'A basement finish that made the whole space feel cleaner and more usable.','desc':'Real Cascade Painting basement floor coating and wall refresh project in Montgomery County, PA with a clean gray coated concrete floor.','image':'basement','kicker':'Montgomery County · Basement coating','lead':'Exposed utilities and an open ceiling can stay honest while the walls and floor still feel deliberate. The coated slab gave this basement a cleaner visual base and a more finished working surface.','scope':['Concrete floor preparation and coating','Wall refresh','Detail work around utilities and posts','Final cleanup and closeout'],'gallery':['basement','basement-alt','garage-alt'],
        'process':'Basements often have more surface variables than a finished room: exposed utilities, masonry, concrete, moisture history and previous coatings. The project was approached as a system. Cleaning and floor preparation came before the finish layer, while wall work was coordinated around the open ceiling and mechanical elements rather than pretending they were not there.',
        'service':'/floor-coatings-lansdale-pa/','service_label':'Floor coatings'
    }
]


def build_resources():
    cards = ''.join(f'''<a class="guide-card" href="/resources/{r['slug']}/"><div class="guide-card-media">{img(r['image'],r['h1'],'','lazy',None,'(max-width: 760px) 100vw, 32vw')}</div><div class="guide-card-copy"><span>Homeowner guide</span><h2>{r['h1']}</h2><p>{r['lead']}</p><b>Read guide →</b></div></a>''' for r in RESOURCES)
    body = breadcrumb_html([('Resources','/resources/')]) + f'''<section class="resource-index-hero"><div class="wrap"><p class="eyebrow">Cascade field notes</p><h1>Useful answers before anyone opens a paint can.</h1><p>Practical guidance on preparation, finishes and project decisions — written to help homeowners understand the work, not to turn every question into a sales pitch.</p></div></section><section class="guide-index"><div class="wrap guide-index-grid">{cards}</div></section><section class="inline-cta"><div class="wrap inline-cta-grid"><h2>Have a project-specific question?</h2><div><p>Send the details and we can talk through the surfaces, timing and next step.</p><a class="btn btn-primary" href="/estimate/">Request an Estimate <span>↗</span></a></div></div></section>'''
    bread = breadcrumb_schema([('Home',DOMAIN+'/'),('Resources',DOMAIN+'/resources/')])
    write_page('resources/index.html', shell('Painting Resources for Homeowners | Cascade Painting','Practical painting guides from Cascade Painting covering interior prep, cabinet refinishing, paint sheen, exterior prep and wallpaper removal.','/resources/',body,'living-room-wide','',False,bread))

    for r in RESOURCES:
        path=f"/resources/{r['slug']}/"
        sections=''.join(f'<section><h2>{h}</h2><p>{p}</p></section>' for h,p in r['sections'])
        body = breadcrumb_html([('Resources','/resources/'),(r['h1'],path)]) + article_hero('Cascade field notes',r['h1'],r['lead'],r['image'],r['h1']) + f'''<section class="guide-article"><div class="wrap guide-article-grid"><article><div class="article-toc"><strong>In this guide</strong>{''.join(f'<a href="#guide-{i}">{h}</a>' for i,(h,_) in enumerate(r['sections'],1))}</div>{''.join(f'<section id="guide-{i}"><h2>{h}</h2><p>{p}</p></section>' for i,(h,p) in enumerate(r['sections'],1))}<div class="article-callout"><p class="eyebrow">Related service</p><h2>Want help applying this to your home?</h2><p>The guide is general. Your actual surface condition, access and goals determine the scope.</p><a class="btn btn-primary" href="{r['service']}">Explore {r['service_label']} →</a></div></article><aside class="article-aside"><div><p class="eyebrow">Planning a project?</p><h3>Share the room, surface and timing.</h3><p>We will use the details to make the first conversation more useful.</p><a class="btn btn-primary" href="/estimate/">Request an Estimate</a></div><div><strong>More homeowner guides</strong>{''.join(f'<a href="/resources/{other["slug"]}/">{other["h1"]} →</a>' for other in RESOURCES if other['slug']!=r['slug'])}</div></aside></div></section>'''
        bread=breadcrumb_schema([('Home',DOMAIN+'/'),('Resources',DOMAIN+'/resources/'),(r['h1'],DOMAIN+path)])
        write_page(f"resources/{r['slug']}/index.html", shell(r['title'],r['desc'],path,body,r['image'],'',True,bread,True))


def build_projects():
    for p in PROJECTS:
        path=f"/projects/{p['slug']}/"
        gallery=''.join(f'<figure>{img(n,p["h1"],"", "lazy",None,"(max-width: 760px) 100vw, 50vw")}</figure>' for n in p['gallery'])
        body = breadcrumb_html([('Projects','/projects/'),(p['h1'],path)]) + f'''<section class="project-detail-hero"><div class="wrap"><p class="eyebrow">{p['kicker']}</p><h1>{p['h1']}</h1><p>{p['lead']}</p></div><div class="project-detail-hero-media">{img(p['image'],p['h1'],'','eager','high','100vw')}</div></section><section class="project-detail-body"><div class="wrap project-detail-grid"><div><p class="eyebrow">The project</p><h2>A finish that works with the space already there.</h2><p class="lead-copy">{p['process']}</p><div class="project-scope"><p class="eyebrow">Scope highlights</p>{''.join(f'<div><span>✓</span><p>{x}</p></div>' for x in p['scope'])}</div></div><aside class="project-facts"><span>Project type</span><strong>{p['service_label']}</strong><span>Area</span><strong>Montgomery County, PA</strong><span>Photography</span><strong>Real Cascade project</strong><a class="btn btn-primary" href="/estimate/">Plan a similar project</a></aside></div></section><section class="project-gallery-wide"><div class="wrap"><p class="eyebrow">Finished space</p><div class="project-detail-gallery">{gallery}</div></div></section><section class="related-strip"><div class="wrap related-strip-grid"><div><p class="eyebrow">Related service</p><h2>{p['service_label']}</h2><p>See how Cascade approaches preparation, scope and finish work for this type of project.</p></div><a class="btn btn-ghost" href="{p['service']}">Explore the service →</a></div></section><section class="inline-cta"><div class="wrap inline-cta-grid"><h2>Have a space you want us to think through?</h2><div><p>Share the basics and we will help you define the next step.</p><a class="btn btn-primary" href="/estimate/">Request an Estimate <span>↗</span></a></div></div></section>'''
        bread=breadcrumb_schema([('Home',DOMAIN+'/'),('Projects',DOMAIN+'/projects/'),(p['h1'],DOMAIN+path)])
        write_page(f"projects/{p['slug']}/index.html", shell(p['title'],p['desc'],path,body,p['image'],'Projects',True,bread,True))


def write_page(path, text):
    p=PUBLIC/path
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(text,encoding='utf-8')


def service_related_data(path):
    mapping = {
        'interior-painting-lansdale-pa': ('/projects/north-wales-living-room-refresh/','North Wales living room project','/resources/interior-painting-preparation-guide/','Interior painting preparation guide',['Surface repairs and patching','Furniture and floor protection','Walls, ceilings and trim included in scope']),
        'exterior-painting-lansdale-pa': ('/projects/garage-floor-coating-refresh/','See recent exterior & utility-space work','/resources/exterior-painting-prep-pennsylvania/','Exterior preparation in Pennsylvania',['Substrate and existing coating condition','Scraping, caulking and priming needs','Weather and access constraints']),
        'cabinet-refinishing-lansdale-pa': ('/projects/north-wales-dining-room-refresh/','See finished interior detail work','/resources/cabinet-refinishing-vs-replacement/','Cabinet refinishing vs. replacement',['Condition of doors and boxes','Degreasing and surface prep','Hardware, color and surrounding finishes']),
        'wallpaper-removal-drywall-repair': ('/projects/north-wales-dining-room-refresh/','See a finished North Wales interior','/resources/wallpaper-removal-wall-prep/','Wallpaper removal and wall preparation',['Hidden wall condition after removal','Adhesive cleanup and damaged paper','Repair, sanding and primer requirements']),
        'floor-coatings-lansdale-pa': ('/projects/garage-floor-coating-refresh/','Garage coating project','/resources/exterior-painting-prep-pennsylvania/','Why surface preparation matters',['Concrete condition and contamination','Existing coating or moisture history','Return-to-service timing']),
        'commercial-painting-lansdale-pa': ('/projects/basement-concrete-coating-refresh/','Large-space coating project','/resources/interior-painting-preparation-guide/','Planning occupied-space painting',['Access and operating-hour constraints','Phasing and drying time','Written scope and closeout requirements'])
    }
    return mapping.get(path)


def enhance_existing_pages():
    html_files=list(PUBLIC.rglob('*.html'))
    for p in html_files:
        text=p.read_text(encoding='utf-8')
        # Fingerprint stable assets with a deployment version so they can be cached aggressively.
        text=re.sub(r'(["\'](?:\.\./)*/?assets/site\.css)(?:\?[^"\']*)?(["\'])', rf'\1?v={ASSET_VERSION}\2', text)
        text=re.sub(r'(["\'](?:\.\./)*/?assets/site\.js)(?:\?[^"\']*)?(["\'])', rf'\1?v={ASSET_VERSION}\2', text)
        # Add Resources to the Company column in the footer, never the primary navigation.
        if 'site-footer' in text:
            before, footer_part = text.split('<footer class="site-footer">', 1)
            if '>Resources</a>' not in footer_part and '>Service Areas</a>' in footer_part:
                footer_part = footer_part.replace('>Service Areas</a>', '>Service Areas</a><a href="/resources/">Resources</a>', 1)
            text = before + '<footer class="site-footer">' + footer_part
        p.write_text(text,encoding='utf-8')

    # Home: add project stories and educational pathways without making the page longer than necessary.
    home=PUBLIC/'index.html'
    text=home.read_text(encoding='utf-8')
    if 'home-project-stories' not in text:
        marker='<section class="standard-band">'
        section=f'''<section class="home-project-stories"><div class="wrap"><div class="section-title-row"><div><p class="eyebrow">Project stories</p><h2>Real rooms. Real scopes. More than a gallery.</h2></div><a class="text-link" href="/projects/">View all project work →</a></div><div class="home-story-grid"><a href="/projects/north-wales-living-room-refresh/">{img('living-room-wide','North Wales living room painted by Cascade Painting','','lazy',None,'(max-width: 760px) 100vw, 52vw')}<div><span>North Wales · Interior</span><h3>Light, architecture and a quieter palette.</h3><p>See what mattered beyond the color choice.</p></div></a><a href="/projects/garage-floor-coating-refresh/">{img('garage','Finished garage painting and floor coating by Cascade Painting','','lazy',None,'(max-width: 760px) 100vw, 42vw')}<div><span>Garage · Coating</span><h3>A utility space finished like part of the home.</h3><p>See the scope and surface considerations.</p></div></a></div></div></section>'''
        text=text.replace(marker,section+marker,1)
    if 'home-resource-strip' not in text:
        marker='<section class="final-cta">'
        strip='''<section class="home-resource-strip"><div class="wrap home-resource-grid"><div><p class="eyebrow">Planning before hiring</p><h2>Understand the project before you price it.</h2></div><div class="home-resource-links"><a href="/resources/interior-painting-preparation-guide/"><strong>Interior prep guide</strong><span>What to move, repair and decide first →</span></a><a href="/resources/cabinet-refinishing-vs-replacement/"><strong>Cabinets: refinish or replace?</strong><span>How to tell which project you need →</span></a><a href="/resources/choosing-paint-sheen/"><strong>Choosing paint sheen</strong><span>A practical room-by-room framework →</span></a></div></div></section>'''
        text=text.replace(marker,strip+marker,1)
    home.write_text(text,encoding='utf-8')

    # Projects overview: make cards actionable and point them to full project stories.
    projects=PUBLIC/'projects'/'index.html'
    if projects.exists():
        text=projects.read_text(encoding='utf-8')
        links=[
            ('North Wales, PA · Interior painting','/projects/north-wales-living-room-refresh/'),
            ('North Wales · Dining room','/projects/north-wales-dining-room-refresh/'),
            ('Garage · Floor coating','/projects/garage-floor-coating-refresh/'),
            ('Basement · Coating','/projects/basement-concrete-coating-refresh/')
        ]
        for label,href in links:
            # add a detail link inside matching project story cards without restructuring the existing visual grid
            pattern=re.escape(f'<span>{label}</span>')
            repl=f'<span>{label}</span><a class="project-detail-link" href="{href}">Project details →</a>'
            text=re.sub(pattern,repl,text,count=1)
        projects.write_text(text,encoding='utf-8')

    # Service pages: deepen content and connect services -> projects -> educational resources.
    for slug in ['interior-painting-lansdale-pa','exterior-painting-lansdale-pa','cabinet-refinishing-lansdale-pa','commercial-painting-lansdale-pa','floor-coatings-lansdale-pa','wallpaper-removal-drywall-repair']:
        p=PUBLIC/slug/'index.html'
        if not p.exists(): continue
        text=p.read_text(encoding='utf-8')
        data=service_related_data(slug)
        if data and 'service-depth-section' not in text:
            proj,proj_label,guide,guide_label,factors=data
            section=f'''<section class="service-depth-section"><div class="wrap service-depth-grid"><div><p class="eyebrow">Scope before price</p><h2>What shapes the project.</h2><p>A useful estimate is tied to the actual condition of the surfaces and how the space has to function while the work is underway.</p><div class="scope-grid">{''.join(f'<div><span>0{i}</span><strong>{x}</strong></div>' for i,x in enumerate(factors,1))}</div></div><aside class="service-related-card"><p class="eyebrow">Keep exploring</p><a href="{proj}"><span>Real project</span><strong>{proj_label}</strong><b>See the work →</b></a><a href="{guide}"><span>Homeowner guide</span><strong>{guide_label}</strong><b>Read the guide →</b></a></aside></div></section>'''
            text=text.replace('<section class="faq-section">',section+'<section class="faq-section">',1)
        # Give estimate links service context; the form can preselect from this query parameter.
        service_name={
            'interior-painting-lansdale-pa':'Interior Painting','exterior-painting-lansdale-pa':'Exterior Painting','cabinet-refinishing-lansdale-pa':'Cabinet Refinishing','commercial-painting-lansdale-pa':'Commercial','floor-coatings-lansdale-pa':'Floor Coating','wallpaper-removal-drywall-repair':'Drywall / Wallpaper'
        }[slug]
        text=re.sub(r'href="(?:\.\./)?estimate/"', f'href="/estimate/?service={service_name.replace(" ","%20").replace("/","%2F")}"', text)
        p.write_text(text,encoding='utf-8')


def update_support_files():
    # sitemap: all indexable HTML except privacy/404; stable sort with homepage first.
    urls=[]
    for p in PUBLIC.rglob('index.html'):
        rel=p.relative_to(PUBLIC)
        path='/' if str(rel)=='index.html' else '/'+str(rel.parent).replace('\\','/')+'/'
        if path=='/privacy/': continue
        urls.append(path)
    urls=sorted(set(urls), key=lambda x:(x!='/','resources/' in x, x))
    sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{DOMAIN}{u}</loc><lastmod>{TODAY}</lastmod></url>\n' for u in urls)+'</urlset>'
    (PUBLIC/'sitemap.xml').write_text(sitemap,encoding='utf-8')

    # image sitemap from actually embedded project imagery.
    rows=[]
    for u in urls:
        p=PUBLIC/'index.html' if u=='/' else PUBLIC/u.strip('/')/'index.html'
        text=p.read_text(encoding='utf-8')
        imgs=[]
        for src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"',text,re.I):
            if '/images/' not in src: continue
            filename=src.split('/images/')[-1].split('?')[0]
            if filename.startswith(('logo','favicon','apple-touch')): continue
            absolute=DOMAIN+'/images/'+filename
            if absolute not in imgs: imgs.append(absolute)
        if imgs:
            rows.append('<url><loc>'+DOMAIN+u+'</loc>'+''.join(f'<image:image><image:loc>{x}</image:loc></image:image>' for x in imgs)+'</url>')
    image_sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'+'\n'.join(rows)+'\n</urlset>'
    (PUBLIC/'image-sitemap.xml').write_text(image_sitemap,encoding='utf-8')

    # Versioned assets can be cached hard because every deployment changes the query string in HTML.
    headers='''/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Frame-Options: SAMEORIGIN
  Cross-Origin-Opener-Policy: same-origin
  Strict-Transport-Security: max-age=31536000; includeSubDomains

/assets/*
  Cache-Control: public, max-age=31536000, immutable

/images/*
  Cache-Control: public, max-age=2592000, stale-while-revalidate=604800

/*.html
  Cache-Control: public, max-age=0, must-revalidate
'''
    (PUBLIC/'_headers').write_text(headers,encoding='utf-8')

    # Expand llms.txt with useful canonical content hubs.
    llms=(PUBLIC/'llms.txt').read_text(encoding='utf-8') if (PUBLIC/'llms.txt').exists() else '# Cascade Painting\n'
    if 'Homeowner resources:' not in llms:
        llms += '\nHomeowner resources:\n- '+DOMAIN+'/resources/\n- '+DOMAIN+'/resources/interior-painting-preparation-guide/\n- '+DOMAIN+'/resources/cabinet-refinishing-vs-replacement/\n- '+DOMAIN+'/resources/choosing-paint-sheen/\n- '+DOMAIN+'/resources/exterior-painting-prep-pennsylvania/\n- '+DOMAIN+'/resources/wallpaper-removal-wall-prep/\n\nProject stories:\n- '+DOMAIN+'/projects/north-wales-living-room-refresh/\n- '+DOMAIN+'/projects/north-wales-dining-room-refresh/\n- '+DOMAIN+'/projects/garage-floor-coating-refresh/\n- '+DOMAIN+'/projects/basement-concrete-coating-refresh/\n'
    (PUBLIC/'llms.txt').write_text(llms,encoding='utf-8')


def update_privacy():
    p=PUBLIC/'privacy'/'index.html'
    if not p.exists(): return
    text=p.read_text(encoding='utf-8')
    if 'first-party interaction events' not in text:
        needle='<h2>Third-party services</h2>'
        addition='<h2>Site measurement</h2><p>The site may record limited first-party interaction events such as page views, estimate-button clicks, phone-link clicks and form progress so Cascade Painting can understand which pages help visitors find what they need. This measurement is designed without cross-site tracking or advertising profiles. Campaign parameters and the page that led to an inquiry may be retained with that inquiry so marketing sources can be evaluated.</p>'
        text=text.replace(needle,addition+needle,1)
    p.write_text(text,encoding='utf-8')


def append_css():
    p=PUBLIC/'assets'/'site.css'
    text=p.read_text(encoding='utf-8')
    marker='/* V4 PRODUCTION OPTIMIZATION */'
    if marker in text:
        text=text.split(marker)[0].rstrip()+'\n'
    extra=r'''
/* V4 PRODUCTION OPTIMIZATION */
html{scrollbar-gutter:stable;-webkit-text-size-adjust:100%;text-size-adjust:100%}
body{overflow-x:hidden}
p{max-width:75ch;text-wrap:pretty}.btn,button,a{touch-action:manipulation}
.breadcrumbs{display:flex;align-items:center;gap:9px;padding-top:22px;font-size:.68rem;color:var(--muted)}.breadcrumbs>span{display:none}.breadcrumbs a{display:inline-flex;align-items:center;gap:9px}.breadcrumbs a:not(:last-child):after{content:'/' ;opacity:.38}.breadcrumbs a:last-child{color:var(--ink);font-weight:700}
.home-project-stories{padding:116px 0;background:var(--paper)}.home-story-grid{display:grid;grid-template-columns:1.16fr .84fr;gap:22px}.home-story-grid>a{background:var(--white);border:1px solid var(--line);border-radius:22px;overflow:hidden;box-shadow:var(--shadow-soft);transition:transform .25s ease,box-shadow .25s ease}.home-story-grid>a:hover{transform:translateY(-4px);box-shadow:var(--shadow)}.home-story-grid img{width:100%;aspect-ratio:16/10;object-fit:cover}.home-story-grid>a:last-child img{aspect-ratio:4/3}.home-story-grid a>div{padding:24px 26px 28px}.home-story-grid span,.guide-card-copy>span,.project-detail-link{font-size:.64rem;text-transform:uppercase;letter-spacing:.13em;font-weight:800;color:var(--pine-2)}.home-story-grid h3{font-family:var(--serif);font-size:2rem;line-height:1.05;font-weight:400;margin:8px 0 8px}.home-story-grid p{font-size:.82rem;color:var(--muted);margin:0}
.home-resource-strip{padding:96px 0;background:var(--white);border-top:1px solid var(--line)}.home-resource-grid{display:grid;grid-template-columns:.75fr 1.25fr;gap:70px}.home-resource-grid h2{font-family:var(--serif);font-size:clamp(2.7rem,4.5vw,4.6rem);font-weight:400;line-height:.98;margin:0}.home-resource-links{border-top:1px solid var(--line)}.home-resource-links a{display:grid;grid-template-columns:.7fr 1fr;gap:22px;padding:22px 0;border-bottom:1px solid var(--line);align-items:baseline}.home-resource-links strong{font-family:var(--serif);font-size:1.35rem;font-weight:400}.home-resource-links span{font-size:.74rem;color:var(--muted)}
.service-depth-section{padding:100px 0;background:var(--paper-2);border-block:1px solid var(--line)}.service-depth-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:70px;align-items:start}.service-depth-grid h2{font-family:var(--serif);font-size:clamp(3rem,4.7vw,4.7rem);line-height:.98;font-weight:400;margin:0 0 20px}.service-depth-grid>div>p:not(.eyebrow){color:var(--muted);max-width:700px}.scope-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin-top:34px}.scope-grid>div{background:var(--white);padding:22px}.scope-grid span{display:block;font-size:.58rem;letter-spacing:.14em;color:var(--pine-2);font-weight:800;margin-bottom:26px}.scope-grid strong{font-family:var(--serif);font-size:1.15rem;line-height:1.2;font-weight:400}.service-related-card{background:var(--ink);color:#fff;padding:30px;border-radius:20px;box-shadow:var(--shadow)}.service-related-card .eyebrow{color:var(--river-2)}.service-related-card>a{display:block;padding:20px 0;border-top:1px solid rgba(255,255,255,.17)}.service-related-card>a:first-of-type{margin-top:8px}.service-related-card a span,.service-related-card a b{display:block;font-size:.62rem;text-transform:uppercase;letter-spacing:.12em;color:rgba(255,255,255,.62)}.service-related-card a strong{display:block;font-family:var(--serif);font-size:1.45rem;line-height:1.1;font-weight:400;margin:8px 0 12px}.service-related-card a b{color:var(--river-2)}
.project-detail-link{display:inline-block;margin-top:8px;border-bottom:1px solid currentColor;padding-bottom:2px}.project-detail-link:hover{opacity:.7}
.resource-index-hero{padding:96px 0 74px;background:var(--paper)}.resource-index-hero h1{font-family:var(--serif);font-size:clamp(4rem,7vw,7.2rem);line-height:.9;letter-spacing:-.04em;font-weight:400;margin:0 0 24px;max-width:1020px}.resource-index-hero>div>p:not(.eyebrow){font-size:1.05rem;color:var(--muted);max-width:750px}.guide-index{padding:0 0 120px}.guide-index-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:22px}.guide-card{display:grid;grid-template-columns:.44fr .56fr;min-height:330px;background:var(--white);border:1px solid var(--line);border-radius:22px;overflow:hidden;box-shadow:var(--shadow-soft);transition:transform .25s ease,box-shadow .25s ease}.guide-card:hover{transform:translateY(-3px);box-shadow:var(--shadow)}.guide-card-media{min-height:100%}.guide-card-media img{width:100%;height:100%;object-fit:cover}.guide-card-copy{padding:30px}.guide-card-copy h2{font-family:var(--serif);font-size:2rem;line-height:1.03;font-weight:400;margin:9px 0 14px}.guide-card-copy p{color:var(--muted);font-size:.82rem}.guide-card-copy b{display:inline-block;margin-top:12px;font-size:.7rem}
.article-hero{padding:72px 0 92px}.article-hero-grid{display:grid;grid-template-columns:.92fr 1.08fr;gap:70px;align-items:center}.article-hero h1{font-family:var(--serif);font-size:clamp(3.7rem,5.7vw,6rem);line-height:.92;letter-spacing:-.035em;font-weight:400;margin:0 0 24px}.article-lead{font-size:1rem;color:var(--muted);max-width:650px}.article-meta{display:flex;flex-wrap:wrap;gap:9px 18px;margin-top:28px;font-size:.64rem;text-transform:uppercase;letter-spacing:.1em;font-weight:800;color:var(--muted)}.article-hero-media img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:22px;box-shadow:var(--shadow)}
.guide-article{padding:100px 0 120px;background:var(--white);border-top:1px solid var(--line)}.guide-article-grid{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:90px;align-items:start}.guide-article article>section{padding:46px 0;border-top:1px solid var(--line);scroll-margin-top:145px}.guide-article article>section h2{font-family:var(--serif);font-size:clamp(2.15rem,3.2vw,3.2rem);line-height:1;font-weight:400;margin:0 0 18px}.guide-article article>section p{font-size:1rem;color:#45585f}.article-toc{display:flex;flex-wrap:wrap;gap:9px 18px;padding:0 0 34px}.article-toc strong{width:100%;font-size:.68rem;text-transform:uppercase;letter-spacing:.13em}.article-toc a{font-size:.72rem;color:var(--muted);border-bottom:1px solid var(--line)}.article-aside{position:sticky;top:150px;display:grid;gap:18px}.article-aside>div{padding:26px;border:1px solid var(--line);border-radius:18px;background:var(--paper)}.article-aside h3{font-family:var(--serif);font-size:1.8rem;line-height:1.05;font-weight:400;margin:0 0 14px}.article-aside p{font-size:.78rem;color:var(--muted)}.article-aside>div:last-child{display:grid;gap:12px}.article-aside>div:last-child>strong{font-size:.68rem;text-transform:uppercase;letter-spacing:.12em}.article-aside>div:last-child a{font-size:.72rem;border-top:1px solid var(--line);padding-top:11px}.article-callout{margin-top:48px;padding:34px;background:var(--paper);border-radius:18px;border:1px solid var(--line)}.article-callout h2{font-family:var(--serif);font-size:2.3rem;font-weight:400;line-height:1;margin:0 0 14px}.article-callout .btn{margin-top:12px}
.project-detail-hero{padding:72px 0 0}.project-detail-hero>.wrap{padding-bottom:54px}.project-detail-hero h1{font-family:var(--serif);font-size:clamp(4rem,6.4vw,7rem);line-height:.9;letter-spacing:-.04em;font-weight:400;margin:0 0 22px;max-width:1080px}.project-detail-hero>.wrap>p:not(.eyebrow){font-size:1.05rem;color:var(--muted);max-width:760px}.project-detail-hero-media img{width:100%;height:min(70vw,760px);object-fit:cover}.project-detail-body{padding:110px 0}.project-detail-grid{display:grid;grid-template-columns:1fr 320px;gap:90px}.project-detail-grid h2{font-family:var(--serif);font-size:clamp(3rem,4.5vw,4.6rem);font-weight:400;line-height:.98;margin:0 0 22px}.project-scope{margin-top:40px;border-top:1px solid var(--line)}.project-scope>div{display:grid;grid-template-columns:32px 1fr;gap:12px;padding:14px 0;border-bottom:1px solid var(--line)}.project-scope span{color:var(--pine-2);font-weight:800}.project-scope p{margin:0}.project-facts{display:grid;align-content:start;padding:28px;background:var(--paper-2);border-radius:18px;position:sticky;top:150px}.project-facts span{font-size:.6rem;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);margin-top:18px}.project-facts span:first-child{margin-top:0}.project-facts strong{font-family:var(--serif);font-size:1.25rem;font-weight:400;padding-bottom:15px;border-bottom:1px solid var(--line)}.project-facts .btn{margin-top:26px}.project-gallery-wide{padding:0 0 120px}.project-gallery-wide>.wrap>.eyebrow{margin-bottom:24px}.project-detail-gallery{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}.project-detail-gallery figure{margin:0}.project-detail-gallery img{width:100%;height:100%;min-height:450px;object-fit:cover;border-radius:18px}.project-detail-gallery figure:first-child{grid-row:span 2}.related-strip{padding:72px 0;background:var(--paper-2);border-block:1px solid var(--line)}.related-strip-grid{display:flex;align-items:end;justify-content:space-between;gap:50px}.related-strip h2{font-family:var(--serif);font-size:3rem;font-weight:400;margin:0 0 10px}.related-strip p{color:var(--muted)}
/* V4.1 HERO REFINEMENT */
.hero-full-inner.wrap{width:100%;max-width:none;margin-inline:0;padding-left:clamp(28px,5vw,96px);padding-right:clamp(28px,5vw,96px)}
.hero-full-copy{width:100%;max-width:none;text-align:left}
.hero-full-copy h1{width:100%;max-width:none;font-size:clamp(4.7rem,6.5vw,7.25rem);line-height:.86;letter-spacing:-.045em;text-align:left;text-wrap:initial;margin-bottom:18px}
.hero-full-copy h1>span{display:block;white-space:nowrap}
.hero-full-copy h1>em{display:block;margin-top:.02em}
.hero-full-copy .hero-lead{margin-bottom:15px}
.hero-full-copy .hero-actions{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
@media(max-width:1100px){.hero-full-inner.wrap{padding-left:32px;padding-right:32px}.hero-full-copy h1{font-size:clamp(4.2rem,6.6vw,5.6rem)}}
@media(max-width:900px){.hero-full-inner.wrap{padding-left:24px;padding-right:24px}.hero-full-copy h1{font-size:clamp(4rem,9.3vw,5.2rem)}.hero-full-copy h1>span{white-space:normal}}
@media(max-width:620px){.hero-full-inner.wrap{padding-left:18px;padding-right:18px}.hero-full-copy h1{font-size:clamp(3.55rem,13.5vw,4.85rem);line-height:.88}.hero-full-copy h1>span{white-space:normal}.hero-full-copy h1>em{margin-top:0}.hero-full-copy .hero-lead{margin-bottom:12px}}
@media(max-width:980px){.home-story-grid,.home-resource-grid,.service-depth-grid,.article-hero-grid,.guide-article-grid,.project-detail-grid{grid-template-columns:1fr}.guide-index-grid{grid-template-columns:1fr}.guide-card{grid-template-columns:.42fr .58fr}.article-aside,.project-facts{position:static}.scope-grid{grid-template-columns:1fr 1fr 1fr}.project-detail-gallery{grid-template-columns:1fr 1fr}.project-detail-gallery figure:first-child{grid-row:auto;grid-column:1/-1}.home-resource-grid{gap:38px}.service-depth-grid{gap:38px}.article-hero-grid{gap:38px}.guide-article-grid{gap:50px}.project-detail-grid{gap:50px}}
@media(max-width:620px){.home-project-stories,.service-depth-section,.guide-article,.project-detail-body{padding-block:76px}.home-story-grid,.project-detail-gallery{grid-template-columns:1fr}.home-story-grid>a:last-child img,.home-story-grid img{aspect-ratio:4/3}.home-resource-strip{padding:72px 0}.home-resource-links a{grid-template-columns:1fr;gap:4px}.scope-grid{grid-template-columns:1fr}.guide-index{padding-bottom:78px}.guide-card{grid-template-columns:1fr}.guide-card-media img{aspect-ratio:16/10}.resource-index-hero{padding:60px 0 48px}.resource-index-hero h1{font-size:3.7rem}.article-hero{padding:52px 0 66px}.article-hero h1{font-size:3.55rem}.article-meta{display:grid}.guide-article article>section{padding:36px 0}.article-callout{padding:24px}.project-detail-hero{padding-top:54px}.project-detail-hero h1{font-size:3.7rem}.project-detail-hero-media img{height:62svh;min-height:430px}.project-detail-gallery img{min-height:320px}.related-strip-grid{display:grid}.breadcrumbs{padding-top:14px;white-space:nowrap;overflow-x:auto;scrollbar-width:none}}
'''
    p.write_text(text+extra,encoding='utf-8')


def append_js():
    p=PUBLIC/'assets'/'site.js'
    text=p.read_text(encoding='utf-8')
    # Insert extra logic before the final IIFE close.
    marker='// V4 PRODUCTION OPTIMIZATION'
    if marker in text:
        text=text.split(marker)[0].rstrip()
        if text.endswith('})();'):
            text=text[:-5].rstrip()
    elif text.rstrip().endswith('})();'):
        text=text.rstrip()[:-5].rstrip()
    extra=r'''

  // V4 PRODUCTION OPTIMIZATION
  // First-party, session-scoped measurement. No cross-site ID, no fingerprinting, no ad profile.
  const sessionKey = 'cascade_session_id';
  let sessionId = '';
  try {
    sessionId = sessionStorage.getItem(sessionKey) || crypto.randomUUID();
    sessionStorage.setItem(sessionKey, sessionId);
  } catch (_) {}
  const firstPartyEvent = (event, detail = {}) => {
    if (!['cascadepaintingpa.com','www.cascadepaintingpa.com'].includes(location.hostname)) return;
    const payload = {
      event,
      sessionId,
      path: location.pathname.slice(0, 500),
      referrer: document.referrer.slice(0, 1000),
      detail,
      ts: new Date().toISOString()
    };
    const body = JSON.stringify(payload);
    try {
      if (navigator.sendBeacon) {
        const blob = new Blob([body], { type: 'application/json' });
        if (navigator.sendBeacon('/api/event', blob)) return;
      }
      fetch('/api/event', { method:'POST', headers:{'Content-Type':'application/json'}, body, keepalive:true }).catch(() => {});
    } catch (_) {}
  };

  const idle = window.requestIdleCallback || (cb => setTimeout(cb, 900));
  idle(() => firstPartyEvent('page_view', { title: document.title.slice(0, 180) }));

  qsa('a[href^="mailto:"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('email_click')));
  qsa('a[href*="google.com/maps"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('google_profile_click')));
  qsa('a[href^="/projects/"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('project_view_click', { href: link.getAttribute('href') })));
  qsa('a[href^="/resources/"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('resource_click', { href: link.getAttribute('href') })));
  qsa('a[href^="tel:"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('phone_click')));
  qsa('a[href*="/estimate/"]').forEach(link => link.addEventListener('click', () => firstPartyEvent('estimate_cta_click', { href: link.getAttribute('href') })));

  // Measure meaningful scroll depth once per page.
  const scrollMarks = new Set();
  const onDepth = () => {
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    const pct = Math.round((scrollY / max) * 100);
    [50,90].forEach(mark => {
      if (pct >= mark && !scrollMarks.has(mark)) {
        scrollMarks.add(mark);
        firstPartyEvent('scroll_depth', { percent: mark });
      }
    });
  };
  addEventListener('scroll', onDepth, { passive:true });

  // Make the estimate experience resilient: prefill service context and keep an in-session draft.
  if (form) {
    const draftKey = 'cascade_estimate_draft';
    const serviceFromUrl = new URLSearchParams(location.search).get('service');
    const serviceFromReferrer = (() => {
      try {
        const path = new URL(document.referrer).pathname;
        const map = {
          '/interior-painting-lansdale-pa/':'Interior Painting',
          '/exterior-painting-lansdale-pa/':'Exterior Painting',
          '/cabinet-refinishing-lansdale-pa/':'Cabinet Refinishing',
          '/wallpaper-removal-drywall-repair/':'Drywall / Wallpaper',
          '/floor-coatings-lansdale-pa/':'Floor Coating',
          '/commercial-painting-lansdale-pa/':'Commercial'
        };
        return map[path] || '';
      } catch (_) { return ''; }
    })();
    const allowedServices = ['Interior Painting','Exterior Painting','Cabinet Refinishing','Drywall / Wallpaper','Floor Coating','Commercial'];
    const desiredService = allowedServices.includes(serviceFromUrl) ? serviceFromUrl : serviceFromReferrer;
    if (desiredService) {
      const radio = qs(`input[name="projectType"][value="${CSS.escape(desiredService)}"]`, form);
      if (radio) radio.checked = true;
    }

    try {
      const draft = JSON.parse(sessionStorage.getItem(draftKey) || '{}');
      Object.entries(draft).forEach(([name,value]) => {
        if (name === 'consent' || name === 'website') return;
        const fields = qsa(`[name="${CSS.escape(name)}"]`, form);
        fields.forEach(field => {
          if (field.type === 'radio') field.checked = field.value === value;
          else if (!field.value) field.value = value;
        });
      });
    } catch (_) {}

    const saveDraft = () => {
      const data = {};
      qsa('input,select,textarea', form).forEach(field => {
        if (!field.name || ['consent','website'].includes(field.name)) return;
        if (field.type === 'radio') { if (field.checked) data[field.name] = field.value; }
        else data[field.name] = field.value;
      });
      try { sessionStorage.setItem(draftKey, JSON.stringify(data)); } catch (_) {}
    };
    qsa('input,select,textarea', form).forEach(field => {
      field.addEventListener('change', saveDraft);
      if (field.tagName === 'TEXTAREA' || field.type === 'text' || field.type === 'email' || field.type === 'tel') field.addEventListener('input', saveDraft);
    });
    qsa('[data-next]', form).forEach(button => button.addEventListener('click', () => firstPartyEvent('estimate_step_continue', { step })));
    form.addEventListener('submit', () => firstPartyEvent('estimate_submit_attempt'));
    window.addEventListener('cascade:conversion', event => {
      if (event.detail?.event === 'lead_submit_success') {
        try { sessionStorage.removeItem(draftKey); } catch (_) {}
        firstPartyEvent('lead_submit_success', { projectType: event.detail.projectType || '' });
      }
    });
  }

  // Warm the estimate page after the critical rendering path so a later CTA feels instant.
  idle(() => {
    if (!location.pathname.startsWith('/estimate')) {
      const prefetch = document.createElement('link');
      prefetch.rel = 'prefetch';
      prefetch.href = '/estimate/';
      document.head.appendChild(prefetch);
    }
  });
})();
'''
    p.write_text(text+extra,encoding='utf-8')


def update_schema_and_functions():
    schema='''CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  name TEXT NOT NULL,
  phone TEXT NOT NULL,
  email TEXT NOT NULL,
  project_type TEXT NOT NULL,
  location TEXT NOT NULL,
  timing TEXT NOT NULL,
  details TEXT NOT NULL,
  source TEXT NOT NULL,
  source_page TEXT,
  landing_page TEXT,
  referrer TEXT,
  utm_source TEXT,
  utm_medium TEXT,
  utm_campaign TEXT,
  utm_content TEXT,
  utm_term TEXT,
  gclid TEXT,
  status TEXT NOT NULL DEFAULT 'new'
);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_status_created ON leads(status, created_at DESC);

CREATE TABLE IF NOT EXISTS web_events (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  session_id TEXT,
  event_name TEXT NOT NULL,
  path TEXT NOT NULL,
  referrer TEXT,
  detail_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_web_events_created ON web_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_web_events_event_created ON web_events(event_name, created_at DESC);

CREATE TABLE IF NOT EXISTS lead_rate_limit (
  visitor_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lead_rate_limit_hash_created ON lead_rate_limit(visitor_hash, created_at DESC);
'''
    (ROOT/'schema.sql').write_text(schema,encoding='utf-8')
    mig=ROOT/'migrations'/'0002_v4_production.sql'
    mig.parent.mkdir(parents=True,exist_ok=True)
    mig.write_text('''-- Apply only to an existing V3 D1 database. Fresh databases should use schema.sql.\nALTER TABLE leads ADD COLUMN source_page TEXT;\nALTER TABLE leads ADD COLUMN landing_page TEXT;\nALTER TABLE leads ADD COLUMN referrer TEXT;\nALTER TABLE leads ADD COLUMN utm_source TEXT;\nALTER TABLE leads ADD COLUMN utm_medium TEXT;\nALTER TABLE leads ADD COLUMN utm_campaign TEXT;\nALTER TABLE leads ADD COLUMN utm_content TEXT;\nALTER TABLE leads ADD COLUMN utm_term TEXT;\nALTER TABLE leads ADD COLUMN gclid TEXT;\nALTER TABLE leads ADD COLUMN status TEXT NOT NULL DEFAULT 'new';\nCREATE INDEX IF NOT EXISTS idx_leads_status_created ON leads(status, created_at DESC);\nCREATE TABLE IF NOT EXISTS web_events (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, session_id TEXT, event_name TEXT NOT NULL, path TEXT NOT NULL, referrer TEXT, detail_json TEXT);\nCREATE INDEX IF NOT EXISTS idx_web_events_created ON web_events(created_at DESC);\nCREATE INDEX IF NOT EXISTS idx_web_events_event_created ON web_events(event_name, created_at DESC);\nCREATE TABLE IF NOT EXISTS lead_rate_limit (visitor_hash TEXT NOT NULL, created_at TEXT NOT NULL);\nCREATE INDEX IF NOT EXISTS idx_lead_rate_limit_hash_created ON lead_rate_limit(visitor_hash, created_at DESC);\n''',encoding='utf-8')

    event_js=r'''const reply = (body, status = 200) => new Response(body ? JSON.stringify(body) : null, {
  status,
  headers: { 'content-type':'application/json; charset=utf-8', 'cache-control':'no-store', 'x-content-type-options':'nosniff' }
});
const clean = (value, max = 500) => String(value || '').trim().slice(0, max);
export async function onRequestPost({ request, env }) {
  const origin = request.headers.get('origin');
  const siteOrigin = new URL(request.url).origin;
  if (origin && origin !== siteOrigin) return reply({ ok:false }, 403);
  if (!(request.headers.get('content-type') || '').toLowerCase().includes('application/json')) return reply({ ok:false }, 415);
  let body;
  try { body = await request.json(); } catch { return reply({ ok:false }, 400); }
  const eventName = clean(body?.event, 80);
  const path = clean(body?.path, 500);
  if (!eventName || !path) return reply({ ok:false }, 400);
  if (!env.DB) return new Response(null, { status:204, headers:{'cache-control':'no-store'} });
  const allowed = new Set(['page_view','phone_click','email_click','google_profile_click','project_view_click','resource_click','estimate_cta_click','scroll_depth','estimate_step_continue','estimate_submit_attempt','lead_submit_success']);
  if (!allowed.has(eventName)) return reply({ ok:false }, 400);
  let detail = {};
  if (body.detail && typeof body.detail === 'object' && !Array.isArray(body.detail)) detail = body.detail;
  const detailJson = JSON.stringify(detail).slice(0, 3000);
  try {
    await env.DB.prepare('INSERT INTO web_events (id, created_at, session_id, event_name, path, referrer, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?)')
      .bind(crypto.randomUUID(), new Date().toISOString(), clean(body.sessionId, 100), eventName, path, clean(body.referrer, 1000), detailJson).run();
  } catch (_) { return new Response(null, { status:204, headers:{'cache-control':'no-store'} }); }
  return new Response(null, { status:204, headers:{'cache-control':'no-store'} });
}
export function onRequestGet() { return reply({ ok:false, error:'method_not_allowed' }, 405); }
'''
    f=ROOT/'functions'/'api'/'event.js'; f.parent.mkdir(parents=True,exist_ok=True); f.write_text(event_js,encoding='utf-8')

    lead=ROOT/'functions'/'api'/'lead.js'
    text=lead.read_text(encoding='utf-8')
    # Add optional privacy-preserving D1 rate limiting and richer D1 persistence, with legacy-schema fallback.
    if 'RATE_LIMIT_SALT' not in text:
        insert='''\n  // Optional rate limiting when D1 + RATE_LIMIT_SALT are configured. Raw IP addresses are never stored.\n  if (env.DB && env.RATE_LIMIT_SALT) {\n    try {\n      const ip = request.headers.get('cf-connecting-ip') || '';\n      if (ip) {\n        const bytes = new TextEncoder().encode(`${env.RATE_LIMIT_SALT}:${ip}`);\n        const digest = await crypto.subtle.digest('SHA-256', bytes);\n        const visitorHash = [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2,'0')).join('');\n        const cutoff = new Date(Date.now() - 15 * 60 * 1000).toISOString();\n        const row = await env.DB.prepare('SELECT COUNT(*) AS count FROM lead_rate_limit WHERE visitor_hash = ? AND created_at >= ?').bind(visitorHash, cutoff).first();\n        if (Number(row?.count || 0) >= 5) return json({ ok:false, error:'rate_limited' }, 429);\n        await env.DB.prepare('INSERT INTO lead_rate_limit (visitor_hash, created_at) VALUES (?, ?)').bind(visitorHash, new Date().toISOString()).run();\n      }\n    } catch (_) { /* fail open if the optional rate-limit table has not been migrated yet */ }\n  }\n'''
        text=text.replace("  if (body.website) return json({ ok: true }); // Honeypot: silently accept bots.\n", "  if (body.website) return json({ ok: true }); // Honeypot: silently accept bots.\n"+insert)
    old="""      await env.DB.prepare(`INSERT INTO leads (id, created_at, name, phone, email, project_type, location, timing, details, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`\n        .bind(lead.id, lead.createdAt, lead.name, lead.phone, lead.email, lead.projectType, lead.location, lead.timing, lead.details, lead.source).run();\n      successes.push('database');"""
    new="""      try {\n        await env.DB.prepare(`INSERT INTO leads (id, created_at, name, phone, email, project_type, location, timing, details, source, source_page, landing_page, referrer, utm_source, utm_medium, utm_campaign, utm_content, utm_term, gclid, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')`)\n          .bind(lead.id, lead.createdAt, lead.name, lead.phone, lead.email, lead.projectType, lead.location, lead.timing, lead.details, lead.source, lead.context.sourcePage, lead.context.landingPage, lead.context.referrer, lead.context.utmSource, lead.context.utmMedium, lead.context.utmCampaign, lead.context.utmContent, lead.context.utmTerm, lead.context.gclid).run();\n      } catch (migrationError) {\n        // Backward compatibility if an existing D1 database has not received the V4 migration yet.\n        await env.DB.prepare(`INSERT INTO leads (id, created_at, name, phone, email, project_type, location, timing, details, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)\n          .bind(lead.id, lead.createdAt, lead.name, lead.phone, lead.email, lead.projectType, lead.location, lead.timing, lead.details, lead.source).run();\n      }\n      successes.push('database');"""
    if old in text:
        text=text.replace(old,new)
    text=text.replace("if (response.status === 400 || response.status === 403 || response.status === 413 || response.status === 415)","if (response.status === 400 || response.status === 403 || response.status === 413 || response.status === 415 || response.status === 429)")
    lead.write_text(text,encoding='utf-8')


def write_qa_and_docs():
    tools=ROOT/'tools'; tools.mkdir(exist_ok=True)
    audit=r'''from pathlib import Path
from bs4 import BeautifulSoup
import json, re, sys
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'public'
errors=[]; warnings=[]
pages=[]; titles={}; descs={}; canonicals={}

def page_url(p):
    rel=p.relative_to(PUBLIC)
    return '/' if str(rel)=='index.html' else '/'+str(rel.parent).replace('\\','/')+'/'

for p in PUBLIC.rglob('*.html'):
    s=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    url=page_url(p) if p.name=='index.html' else None
    if p.name=='index.html': pages.append(url)
    if p.name!='404.html':
        if not s.title or not s.title.string: errors.append(f'{p}: missing title')
        d=s.find('meta',attrs={'name':'description'})
        if not d or not d.get('content','').strip(): errors.append(f'{p}: missing meta description')
        c=s.find('link',rel='canonical')
        noindex=bool(s.find('meta',attrs={'name':'robots','content':re.compile('noindex',re.I)}))
        if not noindex and not c: errors.append(f'{p}: missing canonical')
        if url and not noindex:
            h1=s.find_all('h1')
            if len(h1)!=1: errors.append(f'{p}: expected 1 H1, found {len(h1)}')
            if s.title: titles.setdefault(s.title.get_text(strip=True),[]).append(str(p))
            if d: descs.setdefault(d.get('content','').strip(),[]).append(str(p))
            if c: canonicals.setdefault(c.get('href',''),[]).append(str(p))
    for img in s.find_all('img'):
        if img.get('alt') is None: errors.append(f'{p}: image missing alt {img.get("src")}')
        if not img.get('width') or not img.get('height'): errors.append(f'{p}: image missing dimensions {img.get("src")}')
        src=img.get('src','')
        if src.startswith('/') and not src.startswith('//'):
            target=PUBLIC/src.lstrip('/').split('?')[0]
            if not target.exists(): errors.append(f'{p}: missing image {src}')
    for a in s.find_all('a',href=True):
        href=a['href']
        if href.startswith(('/', './', '../')) and not href.startswith('//'):
            raw=href.split('#')[0].split('?')[0]
            if not raw: continue
            if raw.startswith('/'):
                target=PUBLIC/raw.lstrip('/')
            else:
                target=(p.parent/raw).resolve()
                try: target.relative_to(PUBLIC.resolve())
                except ValueError: continue
            if str(target).endswith('/') or target.is_dir(): target=target/'index.html'
            elif target.suffix=='': target=target/'index.html'
            if not target.exists(): errors.append(f'{p}: broken link {href}')
    for tag in s.find_all('script',attrs={'type':'application/ld+json'}):
        try: json.loads(tag.string or tag.get_text())
        except Exception as exc: errors.append(f'{p}: invalid JSON-LD {exc}')

for label,bucket in [('title',titles),('description',descs),('canonical',canonicals)]:
    for value,items in bucket.items():
        if value and len(items)>1: errors.append(f'duplicate {label}: {value} -> {items}')

try:
    tree=ET.parse(PUBLIC/'sitemap.xml'); ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    listed={urlparse(x.text).path for x in tree.findall('.//s:loc',ns)}
    indexable=set()
    for p in PUBLIC.rglob('index.html'):
        s=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
        noindex=bool(s.find('meta',attrs={'name':'robots','content':re.compile('noindex',re.I)}))
        if not noindex: indexable.add(page_url(p))
    missing=indexable-listed; extra=listed-indexable
    if missing: errors.append(f'sitemap missing: {sorted(missing)}')
    if extra: errors.append(f'sitemap extra: {sorted(extra)}')
except Exception as exc: errors.append(f'sitemap parse failed: {exc}')
try: ET.parse(PUBLIC/'image-sitemap.xml')
except Exception as exc: errors.append(f'image sitemap parse failed: {exc}')

for asset in ['assets/site.css','assets/site.js','robots.txt','site.webmanifest','_headers','_redirects']:
    if not (PUBLIC/asset).exists(): errors.append(f'missing required asset {asset}')

print(f'Audited {len(list(PUBLIC.rglob("*.html")))} HTML files; sitemap/indexable pages: {len(indexable)}')
if warnings:
    print('WARNINGS:'); [print(' -',x) for x in warnings]
if errors:
    print('ERRORS:'); [print(' -',x) for x in errors]; sys.exit(1)
print('PASS: internal links, metadata, structured data, images and sitemap coverage are consistent.')
'''
    (tools/'site_audit.py').write_text(audit,encoding='utf-8')
    workflow=ROOT/'.github'/'workflows'/'site-check.yml'; workflow.parent.mkdir(parents=True,exist_ok=True)
    workflow.write_text('''name: Website QA\n\non:\n  push:\n  pull_request:\n\njobs:\n  audit:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.12'\n      - run: pip install beautifulsoup4\n      - run: python build_site.py\n      - run: python tools/site_audit.py\n      - uses: actions/setup-node@v4\n        with:\n          node-version: '22'\n      - run: node --check public/assets/site.js\n''',encoding='utf-8')
    (ROOT/'PRODUCTION-CHECKLIST.md').write_text('''# Cascade Painting — Production Checklist\n\n## Before deploy\n- Run `python build_site.py`.\n- Run `python tools/site_audit.py`.\n- Run `node --check public/assets/site.js`.\n- Keep the existing `.git` directory when replacing project files.\n\n## Cloudflare\n- Build output: `public`.\n- Functions directory: `functions`.\n- Bind D1 as `DB` and apply `schema.sql` for a new database, or `migrations/0002_v4_production.sql` for an existing V3 database.\n- Set `RATE_LIMIT_SALT` to a long random secret if D1 is connected.\n- Configure Resend and/or `CRM_WEBHOOK_URL` so leads have a delivery path.\n\n## Live launch checks\n- Submit one real test lead on desktop and mobile.\n- Click phone/email/estimate CTAs.\n- Confirm the Google Reviews links on Home and Reviews open the correct Business Profile.\n- Test `/404-test` and legacy redirects.\n- Run PageSpeed Insights on Home, Interior Painting and Estimate.\n- Run Google Rich Results Test on Home and one service page.\n- In Search Console: inspect Home, submit `sitemap.xml`, and check indexing after the deployment is crawled.\n- Confirm favicon and social share image on a messaging/social preview.\n\n## Ongoing\n- Add finished project photography as projects close.\n- Publish resource content only when it answers a real homeowner question.\n- Review search queries and landing-page conversions monthly before creating new location pages.\n''',encoding='utf-8')
    (ROOT/'V4-CHANGELOG.md').write_text('''# V4 Production Optimization\n\n- Added full project-story pages using real Cascade photography.\n- Added homeowner resource center and five substantive planning guides.\n- Deepened service pages with scope factors, project proof and related guides.\n- Added first-party, session-scoped conversion measurement with optional D1 persistence.\n- Added in-session estimate-form draft recovery and service prefill.\n- Added D1 attribution columns, lead status, web event table and privacy-preserving optional rate limiting.\n- Added versioned CSS/JS cache strategy and a direct Google Reviews path without a third-party widget.\n- Added automated static QA and a GitHub Actions validation workflow.\n- Expanded sitemap, image sitemap, `llms.txt`, privacy disclosure and production checklist.\n- Preserved the V3 visual system, full-bleed hero, review -> owner-story hierarchy and app-ready `/api/lead` contract.\n''',encoding='utf-8')

    # Update app integration documentation.
    app=ROOT/'APP-INTEGRATION.md'
    app.write_text('''# Cascade App / CRM Integration\n\nThe public site is now prepared to act as the acquisition layer for `app.cascadepaintingpa.com`.\n\n## Lead contract\n`POST /api/lead` creates a lead with customer/project fields plus landing page, source page, referrer, UTM parameters and GCLID. It can persist to D1, send email through Resend, and forward the same normalized lead to `CRM_WEBHOOK_URL`.\n\nRecommended CRM lead stages: `new -> contacted -> estimate_scheduled -> estimate_sent -> won/lost -> scheduled -> completed -> review_requested`.\n\n## First-party website events\n`POST /api/event` can write session-scoped events to the D1 `web_events` table. Current events include page views, phone/email clicks, project/resource clicks, estimate CTA clicks, scroll depth, form progress and successful lead submission. No raw IP address is stored by this endpoint.\n\n## D1\nFor a fresh database use `schema.sql`. For an existing V3 database apply `migrations/0002_v4_production.sql`.\n\n## Rate limiting\nIf `DB` and `RATE_LIMIT_SALT` are configured, the lead endpoint hashes the connecting IP with the private salt and limits repeated form submissions. The raw IP is not persisted.\n\n## Next app phase\nThe app can consume the existing lead schema immediately, then add customer records, estimates, job scheduling, photos/files, products/colors, tasks, invoices, review automation, dashboards and crew/mobile workflows without changing public website URLs.\n''',encoding='utf-8')


def apply():
    build_resources()
    build_projects()
    enhance_existing_pages()
    update_privacy()
    append_css()
    append_js()
    update_schema_and_functions()
    update_support_files()
    write_qa_and_docs()
    print('V4 production optimization applied')


if __name__ == '__main__':
    apply()
