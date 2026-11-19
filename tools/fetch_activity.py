#!/usr/bin/env python3
"""Fetch what has happened lately across the listed projects, for the profile's "What's new" section (P-05, P-06).

Reads each listed repository's public Atom feeds on github.com (releases and commits) and writes data/activity.json:
the latest releases, and the date of the last change by a person to any project. No token is needed.

Safety: only https://github.com/cyberdudeuk/<name>/... is fetched, and only for repository names that match a strict
pattern; a feed carrying a DOCTYPE is refused before parsing (no entity tricks); a feed that fails to load is skipped
and the previous value is kept, so a network blip never empties the profile.

Run: python3 tools/fetch_activity.py ../cyberdudeuk.github.io
"""
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = 'cyberdudeuk'
NAME = re.compile(r'^[A-Za-z0-9._-]{1,100}$')
BOTS = re.compile(r'\[bot\]$|^dependabot|^github-actions', re.I)
ATOM = '{http://www.w3.org/2005/Atom}'
KEEP = 6


def get(url):
    if not url.startswith(f'https://github.com/{OWNER}/'):
        raise ValueError(f'refusing to fetch {url}')
    req = urllib.request.Request(url, headers={'User-Agent': 'cyberdudeuk-profile-refresh'})
    with urllib.request.urlopen(req, timeout=20) as r:  # noqa: S310 (host checked above)
        return r.read(2_000_000).decode('utf-8', 'replace')


def entries(xml):
    if '<!DOCTYPE' in xml.upper():
        raise ValueError('feed carries a DOCTYPE')
    root = ET.fromstring(xml)
    for e in root.findall(f'{ATOM}entry'):
        link = e.find(f'{ATOM}link')
        yield {'title': (e.findtext(f'{ATOM}title') or '').strip(),
               'date': (e.findtext(f'{ATOM}updated') or '')[:10],
               'url': link.get('href') if link is not None else '',
               'author': (e.findtext(f'{ATOM}author/{ATOM}name') or '').strip()}


def short(title, project):
    """P-07: release titles often repeat the project name ("Plainspoken 2.6.0"), which read twice on the profile."""
    rest = title[len(project):].strip(' :-') if title.lower().startswith(project.lower()) else title
    return rest or title


def collect(projects, fetch=get):
    """Latest releases across projects, and the last change by a person. Pure apart from fetch, so it is tested."""
    releases, changes, failed = [], [], []
    for p in projects:
        name = p['repo'].rstrip('/').split('/')[-1]
        if not NAME.match(name) or not p['repo'].startswith(f'https://github.com/{OWNER}/'):
            failed.append(name)
            continue
        try:
            for e in list(entries(fetch(f'https://github.com/{OWNER}/{name}/releases.atom')))[:1]:  # latest only
                releases.append({'project': p['name'], 'release': short(e['title'], p['name']), 'date': e['date'],
                                 'url': e['url']})
            people = [e for e in entries(fetch(f'https://github.com/{OWNER}/{name}/commits.atom'))
                      if e['author'] and not BOTS.search(e['author'])]
            if people:
                changes.append({'project': p['name'], 'date': people[0]['date']})
        except Exception as err:  # noqa: BLE001 (one bad feed must not stop the others)
            failed.append(f'{name}: {err}')
    releases.sort(key=lambda r: r['date'], reverse=True)
    last = max(changes, key=lambda c: c['date']) if changes else None
    return {'releases': releases[:KEEP], 'last_change': last, 'failed': failed}


def main(argv):
    site = Path(argv[1]) if len(argv) > 1 else ROOT.parent / 'cyberdudeuk.github.io'
    projects = json.loads((site / 'data' / 'projects.json').read_text(encoding='utf-8'))['projects']
    target = ROOT / 'data' / 'activity.json'
    old = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
    # The launchpad itself counts as a project change: notes and listings are published there (P-05).
    new = collect(projects + [{'name': 'Public Good Works launchpad', 'repo': f'https://github.com/{OWNER}/{OWNER}.github.io'}])
    out = {'generated': date.today().isoformat(),
           'releases': new['releases'] or old.get('releases', []),
           'last_change': new['last_change'] or old.get('last_change')}
    for f in new['failed']:
        print(f'::warning::skipped {f}')
    if {k: v for k, v in out.items() if k != 'generated'} == {k: v for k, v in old.items() if k != 'generated'}:
        out['generated'] = old.get('generated', out['generated'])  # nothing new: keep the file byte-identical
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'wrote {target.name}: {len(out["releases"])} releases, last change {out["last_change"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
