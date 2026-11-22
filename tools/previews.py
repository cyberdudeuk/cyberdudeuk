#!/usr/bin/env python3
"""Make the gallery preview card for every launchpad project that has none (P-08).

Each card is 1280x640: the launchpad mark, the project's area as a pill, its name, its summary, its status and
licence, its address, the area's icon drawn large and faint, and a bar in the area's colour. It is drawn as a small
HTML page and photographed in headless Chrome, so it uses the same fonts and icons as the launchpad.

Run:   python3 tools/previews.py ../cyberdudeuk.github.io            make the missing and out-of-date cards
       python3 tools/previews.py ../cyberdudeuk.github.io --only ID  remake one card (for example after a rename)
       python3 tools/previews.py ../cyberdudeuk.github.io --check    list missing or out-of-date cards; exit 1 if any
Needs: Chrome (CHROME, default google-chrome), Pillow, and the Inter font (Ubuntu: fonts-inter).

P-08: DAM Policy Explorer and OpenGovernment UK were listed with no preview, because every card was made by hand.
      P-03 kept the README from showing a broken image, so the gap went unnoticed (22 Nov 2026).
P-09: hand-made cards went stale: the Data Quality Commons card still said "OGL v3.0 content" after its content
      became CC BY 4.0. Each card's inputs are now fingerprinted, and a card is remade when they change (22 Nov 2026).
"""
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess  # noqa: S404 (runs Chrome with a fixed argument list, never a shell)
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'previews'
PRINTS = OUT / 'fingerprints.json'  # what each card was made from, so a card is remade when its project changes (P-09)
DESIGN = '1'  # bump to remake every card after changing page()
ID = re.compile(r'^[a-z0-9][a-z0-9.-]{0,80}$')
AMBER = '#e5a53b'
# Each area's colour, sampled from the cards made by hand before this tool existed, so new cards match them.
PALETTE = {'ai': '#4cd3b5', 'standards': '#8eb4ff', 'data': '#f4b45a', 'government': '#f59fc0', 'business': '#e1dc76', 'reuse': '#69d896',
           'knowledge': '#cca5f4', 'skills': '#ff9d84', 'community': '#f7c44f', 'youth': '#7ad6ff', 'experiments': '#bbea82'}
MARK = ('<svg width="40" height="40" viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="11" fill="#162a3a"/>'
        '<path d="M13 14L27 14L20 27Z" fill="none" stroke="#3fc6b1" stroke-width="2"/><circle cx="13" cy="14" r="3.4" fill="#3fc6b1"/>'
        '<circle cx="27" cy="14" r="3.4" fill="#f2b450"/><circle cx="20" cy="27" r="3.4" fill="#8fb3ff"/></svg>')


def launchpad_build(site):
    """The launchpad's own build module, for its icons and status kinds (one source for both pages)."""
    tools = str((site / 'tools').resolve())
    if tools not in sys.path:
        sys.path.insert(0, tools)  # build.py imports its sibling modules
    spec = importlib.util.spec_from_file_location('launchpad_build', site / 'tools' / 'build.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def summary(text, limit=230):
    """Whole sentences, as many as fit four lines of the card; the first sentence always."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    out = parts[0]
    for s in parts[1:]:
        if len(out) + 1 + len(s) > limit:
            break
        out += ' ' + s
    return out


def fingerprint(p, cat):
    """The card's inputs: when any of them changes, the card is out of date."""
    keys = (DESIGN, p['name'], p['summary'], p['status'], p.get('licence', ''), address(p), p['category'], cat.get('label', ''), cat.get('icon', ''))
    return hashlib.sha256(json.dumps(keys).encode('utf-8')).hexdigest()[:16]


def stale(projects, cats):
    """Projects whose card is missing or was made from different data."""
    prints = json.loads(PRINTS.read_text(encoding='utf-8')) if PRINTS.exists() else {}
    return [p['id'] for p in projects
            if not (OUT / f'{p["id"]}.jpg').exists() or prints.get(p['id']) != fingerprint(p, cats.get(p['category'], {}))]


def address(p):
    return re.sub(r'^https?://', '', p.get('site') or p['repo'])


def page(p, cat, kind_label, icons, font_url):
    """The card as one HTML page. Every value from the data is escaped."""
    c = PALETTE.get(p['category'], AMBER)
    ico = icons.get(cat.get('icon', ''), '')
    e = html.escape
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
@font-face{{font-family:SG;src:url({font_url}) format('woff2');font-weight:300 700}}
*{{margin:0;box-sizing:border-box}}
body{{width:1280px;height:640px;overflow:hidden;position:relative;color:#eef3f8;font-family:Inter,system-ui,sans-serif;
background:radial-gradient(70% 90% at 100% 0,{c}1f,transparent 60%),radial-gradient(60% 80% at 0 100%,#16283a,transparent 70%),#0a1823}}
.brand{{position:absolute;left:72px;top:59px;display:flex;gap:14px;align-items:center}}
.brand b{{display:block;font:600 21px SG,sans-serif}}.brand small{{font-size:15px;color:#a9b6c3}}
.pill{{position:absolute;right:72px;top:59px;border:1.5px solid {c};color:{c};border-radius:30px;padding:9px 18px;
font:600 18px SG,sans-serif;display:flex;gap:12px;align-items:center}}
.big{{position:absolute;right:56px;top:96px;width:400px;height:400px;opacity:.16}}
.copy{{position:absolute;left:72px;top:166px;width:760px}}
h1{{font:700 62px/1.08 SG,sans-serif;letter-spacing:-.5px;margin-bottom:26px}}
p{{font-size:24px;line-height:1.45;color:#c9d3dc;width:720px}}
.foot{{position:absolute;left:72px;bottom:57px;display:flex;gap:14px;align-items:center;font-size:18px;color:#a9b6c3;max-width:640px}}
.st{{background:{c};color:#111;font:700 18px SG,sans-serif;border-radius:6px;padding:3px 10px;white-space:nowrap}}
.url{{position:absolute;right:72px;bottom:60px;font:600 19px SG,sans-serif}}
.bar{{position:absolute;left:0;right:0;bottom:0;height:8px;background:linear-gradient(90deg,{c},{AMBER})}}
</style></head><body>
<div class="brand">{MARK}<span><b>Public Good Works</b><small>by cyberdudeuk</small></span></div>
<div class="pill"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
 stroke-linecap="round" stroke-linejoin="round">{ico}</svg>{e(cat.get('label', ''))}</div>
<svg class="big" id="big" viewBox="0 0 24 24" preserveAspectRatio="xMaxYMid meet" fill="none" stroke="{c}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">{ico}</svg>
<script>var g=document.getElementById('big'),b=g.getBBox(),m=1;g.setAttribute('viewBox',[b.x-m,b.y-m,b.width+2*m,b.height+2*m].join(' '));</script>
<div class="copy"><h1>{e(p['name'])}</h1><p>{e(summary(p['summary']))}</p></div>
<div class="foot"><span class="st">{e(kind_label)}</span><span>{e(p.get('licence', ''))}</span></div>
<div class="url">{e(address(p))}</div><div class="bar"></div>
</body></html>'''


def render(site, projects, cats, ids):
    """Photograph each card in headless Chrome and save it as a JPEG next to the others."""
    from PIL import Image
    lp = launchpad_build(site)
    kinds = dict(lp.KINDS)
    chrome = os.environ.get('CHROME') or shutil.which('google-chrome') or 'google-chrome'
    made = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copy(site / 'fonts' / 'space-grotesk-latin-wght.woff2', tmp / 'sg.woff2')
        for p in projects:
            if p['id'] not in ids:
                continue
            if not ID.match(p['id']):
                raise SystemExit(f'refused: project id {p["id"]!r} is not a safe file name')
            src, png = tmp / 'card.html', tmp / 'card.png'
            src.write_text(page(p, cats.get(p['category'], {}), kinds[lp.kind(p['status'])], lp.ICONS, 'sg.woff2'), encoding='utf-8')
            subprocess.run([chrome, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',  # noqa: S603
                            '--force-device-scale-factor=1', '--window-size=1280,640', f'--screenshot={png}', src.as_uri()],
                           check=True, capture_output=True, timeout=60)
            OUT.mkdir(parents=True, exist_ok=True)
            Image.open(png).convert('RGB').save(OUT / f'{p["id"]}.jpg', quality=88)
            made.append(p['id'])
    prints = json.loads(PRINTS.read_text(encoding='utf-8')) if PRINTS.exists() else {}
    prints.update({p['id']: fingerprint(p, cats.get(p['category'], {})) for p in projects if p['id'] in made})
    PRINTS.write_text(json.dumps(dict(sorted(prints.items())), indent=2) + '\n', encoding='utf-8')
    return made


def main(argv):
    site = Path(argv[0]) if argv and not argv[0].startswith('--') else ROOT.parent / 'cyberdudeuk.github.io'
    d = json.loads((site / 'data' / 'projects.json').read_text(encoding='utf-8'))
    cats = {c['id']: c for c in d['categories']}
    missing = stale(d['projects'], cats)
    if '--check' in argv:
        print('every preview is current' if not missing else 'missing or out of date: ' + ', '.join(missing))
        return 1 if missing else 0
    ids = {argv[argv.index('--only') + 1]} if '--only' in argv else set(missing)
    made = render(site, d['projects'], cats, ids)
    print('made: ' + (', '.join(made) if made else 'nothing to make'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
