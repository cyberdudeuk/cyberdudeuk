#!/usr/bin/env python3
"""Build README.md for the cyberdudeuk profile from the launchpad's own register, so the two never disagree.

Source of truth: cyberdudeuk.github.io/data/projects.json and data/owner.json (pass the clone path).
Run:  python3 tools/build_readme.py ../cyberdudeuk.github.io
Check: python3 tools/build_readme.py ../cyberdudeuk.github.io --check   (fails if README.md is out of date)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / 'cyberdudeuk.github.io'
CHECK = '--check' in sys.argv
LAUNCHPAD = 'https://cyberdudeuk.github.io/'
CONTACT = 'https://github.com/cyberdudeuk/cyberdudeuk.github.io/issues/new?template=contact.yml'
ORCID = 'https://orcid.org/0009-0000-5880-7219'
DEV = 'https://dev.to/cyberdudeuk'
LINKEDIN = 'https://www.linkedin.com/in/emanuel'
NOTES = LAUNCHPAD + '#notes'
FEED = LAUNCHPAD + 'feed.xml'
BOARD = 'https://github.com/users/cyberdudeuk/projects/4'
FLAGSHIP = 'github-repos-asset-catalogue'  # the one project to meet first; change the id to change the flagship


def load():
    d = json.loads((SITE / 'data' / 'projects.json').read_text(encoding='utf-8'))
    owner = json.loads((SITE / 'data' / 'owner.json').read_text(encoding='utf-8'))
    return d, owner


def activity():
    """data/activity.json, written by tools/fetch_activity.py; empty when it has not run yet."""
    f = ROOT / 'data' / 'activity.json'
    return json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}


def notes(site, n=3):
    """The latest notes from the launchpad's data/posts.json, newest first, each linked to where it is published."""
    f = site / 'data' / 'posts.json'
    if not f.exists():
        return []
    posts = sorted(json.loads(f.read_text(encoding='utf-8'))['posts'], key=lambda x: x['date'], reverse=True)
    return [(x['title'], x.get('home') or f'{LAUNCHPAD}notes/{x["id"]}.html', x['date']) for x in posts[:n]]


def flagship(d):
    p = next((x for x in d['projects'] if x['id'] == FLAGSHIP), None)
    if not p:
        return ''
    href = p['site'] or p['repo']
    return (f'## Start here\n\n**[{p["name"]}]({href})** is the project to try first. {p["summary"]}\n\n'
            f'[Open it]({href}) · [Repository]({p["repo"]}) · {p["status"]}\n')


def whats_new(act, site):
    """Releases, notes and the board side by side: what changed lately, rebuilt daily (P-06)."""
    rel = '<br>'.join(f'<a href="{r["url"]}">{r["project"]} {r["release"]}</a> · {r["date"]}'
                      for r in act.get('releases', [])[:5]) or 'No releases yet.'
    nts = '<br>'.join(f'<a href="{u}">{t}</a> · {dt}' for t, u, dt in notes(site)) or 'No notes yet.'
    board = (f'<a href="{BOARD}">Public Good Works board</a>: every project with its status, set from its '
             'activity, and a weekly status update.')
    return ('## What\'s new\n\n<table>\n<tr><th width="40%">Latest releases</th><th width="35%">Latest notes</th>'
            '<th width="25%">Working on</th></tr>\n'
            f'<tr><td valign="top">{rel}</td><td valign="top">{nts}<br><a href="{FEED}">Feed</a> · '
            f'<a href="{NOTES}">All notes</a></td><td valign="top">{board}</td></tr>\n</table>\n')


def colophon_date(d, act):
    """P-05: the colophon showed the register's own date (2026-11-15) while projects changed daily, so the page looked
    stale. It now shows the last change by a person to any project, falling back to the register date."""
    last = (act.get('last_change') or {}).get('date')
    return f'last change {last}' if last else f'updated {d["updated"]}'


def card(p):
    """One gallery cell: the project's preview card, linked to its site (or repository when it has no site)."""
    href = p['site'] or p['repo']
    img = f'assets/previews/{p["id"]}.jpg'
    meta = f'<br><sub><a href="{p["repo"]}">Repository</a> · {p["status"]} · {p["licence"]}</sub>'
    if not (ROOT / img).exists():  # P-03: a newly listed project has no preview yet; never publish a broken image
        return f'<a href="{href}"><strong>{p["name"]}</strong></a><br>{p["summary"]}{meta}'
    return (f'<a href="{href}"><img src="{img}" alt="{p["name"]}: {p["summary"].split(". ")[0].rstrip(".")}." width="100%"></a>'
            + meta)


def gallery(d):
    rows, cells = [], [card(p) for p in d['projects']]
    for i in range(0, len(cells), 2):
        pair = cells[i:i + 2] + ([''] if len(cells[i:i + 2]) == 1 else [])
        rows.append('<tr>' + ''.join(f'<td width="50%" valign="top">{c}</td>' for c in pair) + '</tr>')
    return '<table>\n' + '\n'.join(rows) + '\n</table>'


def ways_in(d):
    by_id = {p['id']: p for p in d['projects']}
    out = ['| If you are… | Start with |', '|---|---|']
    labels = {'Beginner': 'New to the topic', 'Intermediate': 'Doing the work day to day',
              'Advanced': 'Building, assuring or reusing'}
    for level, ids in d['ways_in'].items():
        if level.startswith('_'):
            continue
        links = ' · '.join(f'[{by_id[i]["name"]}]({by_id[i]["site"] or by_id[i]["repo"]})' for i in ids if i in by_id)
        out.append(f'| **{labels.get(level, level)}** | {links} |')
    return '\n'.join(out)


def areas(d):
    count = {c['id']: sum(1 for p in d['projects'] if p['category'] == c['id']) for c in d['categories']}
    return ' · '.join(f'{c["label"]} ({count[c["id"]]})' for c in d['categories'] if count[c['id']])


def readme():
    d, owner = load()
    act = activity()
    live = sum(1 for p in d['projects'] if p.get('site'))
    return f'''<!-- Built by tools/build_readme.py from {LAUNCHPAD}data/projects.json. Edit the data, not this file. -->
<a href="{LAUNCHPAD}"><img src="assets/banner.svg" alt="{owner["site_name"]}, by {owner["display_name"]}: {owner["tagline"]}." width="100%"></a>

<p align="center">
<a href="{LAUNCHPAD}"><img alt="Launchpad: {owner['site_name']}" src="https://img.shields.io/badge/launchpad-{owner['site_name'].replace(' ', '_')}-0b6e61?style=for-the-badge"></a>
<a href="{ORCID}"><img alt="ORCID iD" src="https://img.shields.io/badge/ORCID-0009--0000--5880--7219-a6ce39?style=for-the-badge&logo=orcid&logoColor=white"></a>
<a href="{DEV}"><img alt="DEV Community: @cyberdudeuk" src="https://img.shields.io/badge/DEV-@cyberdudeuk-0a0a0a?style=for-the-badge&logo=devdotto&logoColor=white"></a>
<a href="{LINKEDIN}"><img alt="LinkedIn" src="https://img.shields.io/badge/LinkedIn-profile-0a66c2?style=for-the-badge"></a>
<a href="{NOTES}"><img alt="Notes and feed" src="https://img.shields.io/badge/notes-read_and_subscribe-b35c00?style=for-the-badge"></a>
<a href="{BOARD}"><img alt="Project board: status of every project" src="https://img.shields.io/badge/board-project_status-6f42c1?style=for-the-badge"></a>
<a href="#projects"><img alt="{len(d['projects'])} public projects, {live} with a live site" src="https://img.shields.io/badge/projects-{len(d['projects'])}_public_·_{live}_live-1d70b8?style=for-the-badge"></a>
</p>

{owner["about"]}

<!-- TODO(owner): one or two sentences in your own voice about why you build these — the work, the public-good motive,
     what you want people to do next. Kept blank on purpose: owner.json says nothing personal is published unless you write it. -->

**Areas of work:** {areas(d)}

{flagship(d)}
{whats_new(act, SITE)}
## Where else to start

{ways_in(d)}

## Projects

{gallery(d)}

## How every project is built

- **Checked before it ships.** Every repository runs its own checks on each pull request, plus CodeQL and OpenSSF Scorecard.
- **Accessible by default.** Pages are tested with axe-core at several widths, work by keyboard and respect reduced motion.
- **Honest about status.** Each project says plainly whether it is a prototype, proposed or a working tool, and what it is not.
- **Open by default.** Code under open licences; content under the Open Government Licence or Creative Commons where stated.
- **Contact by form only.** No email addresses are published: use the [contact form]({CONTACT}).

## Recognition and open contributions

- **Permanent identifier:** [`w3id.org/dcat-ap-uk`](https://w3id.org/dcat-ap-uk), registered through a merged pull request to
  [perma-id/w3id.org#7100](https://github.com/perma-id/w3id.org/pull/7100).
- **Standards contributions:** issues and pull requests to the
  [UK Cross-Government Metadata Exchange Model](https://github.com/co-cddo/ukgov-metadata-exchange-model) and the
  [Data Standards Authority](https://github.com/alphagov/data-standards-authority) repositories.

<details><summary><strong>Disclaimer, disclosures and transparency</strong></summary>

- These are prototypes and personal public-good projects unless a project says otherwise. Nothing here is official
  government guidance or policy, and no project is endorsed by any department unless it says so.
- Some project text and code were drafted with AI assistance and then checked; each repository says how it is checked.
- Figures and claims link to their sources inside each project. If something is wrong, use the [contact form]({CONTACT}).

</details>

<p align="center"><a href="{LAUNCHPAD}"><img src="assets/qr.svg" alt="QR code for {LAUNCHPAD}" width="96"></a>
&nbsp;&nbsp;<a href="{LAUNCHPAD}"><img src="assets/barcode.svg" alt="Barcode encoding {LAUNCHPAD}" height="72"></a><br>
<sub>{owner["site_name"]} · {LAUNCHPAD} · {colophon_date(d, act)} · register v{d["version"]}</sub></p>
'''


def main():
    text = readme()
    target = ROOT / 'README.md'
    if CHECK:
        if not target.exists() or target.read_text(encoding='utf-8') != text:
            print('README.md is out of date: run tools/build_readme.py'); return 1
        print('README.md is up to date'); return 0
    target.write_text(text, encoding='utf-8')
    print(f'wrote README.md ({len(text)} chars)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
