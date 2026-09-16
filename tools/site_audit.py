from pathlib import Path
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
