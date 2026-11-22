"""Repository checks for the profile page (secure development standard, 15 Nov 2026).

P-01: the repository had no CI at all, so a lint finding or a stale README could merge unnoticed.
P-02: the "projects" badge was a bare <img>, so clicking it on the profile opened the raw SVG on
      camo.githubusercontent.com instead of going anywhere useful (18 Nov 2026).
P-04: the DEV Community profile was listed in the GitHub sidebar but not on the profile README, so the
      two drifted apart; the README must link every public profile the sidebar does (18 Nov 2026).
P-03: a project newly merged into the launchpad has no preview image yet; the README must not show a broken image.
P-05: the colophon said "updated 2026-11-15" (the register's own date) while projects changed every day, so the page
      looked stale. It must show the last change by a person to any project (19 Nov 2026).
P-06: the profile linked neither the notes nor the project board, so visitors could not see what was new or under way;
      LinkedIn and the Zenodo community were missing from the badges too (19 Nov 2026).
P-07: release titles repeat the project name ("Plainspoken 2.6.0"), which read twice in "What's new" (19 Nov 2026).
P-08: DAM Policy Explorer and OpenGovernment UK were listed with no preview card, because every card was made by hand;
      tools/previews.py now makes them and the refresh routine runs it (22 Nov 2026).
P-09: hand-made cards went stale (Data Quality Commons still said "OGL v3.0 content"); each card's inputs are fingerprinted
      and a card is remade when they change (22 Nov 2026).
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / '.github' / 'workflows'


class Checks(unittest.TestCase):
    def test_checks_workflow_lints_tests_and_checks_the_readme(self):
        wf = (WF / 'checks.yml').read_text(encoding='utf-8')
        self.assertIn('ruff check .', wf)
        self.assertIn('unittest discover', wf)
        self.assertIn('build_readme.py', wf)
        self.assertIn('--check', wf)

    def test_every_workflow_declares_read_only_default_permissions(self):
        for f in WF.glob('*.yml'):
            self.assertIn('permissions:\n  contents: read', f.read_text(encoding='utf-8'), f.name)

    def test_readme_links_each_public_profile(self):
        # P-04: profiles shown in the GitHub sidebar must also be linked from the README badges.
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        for url in ('https://orcid.org/0009-0000-5880-7219', 'https://dev.to/cyberdudeuk',
                    'https://www.linkedin.com/in/emanuel'):  # P-06
            self.assertIn(f'<a href="{url}">', readme, url)

    def test_every_readme_image_is_wrapped_in_a_link(self):
        # P-02: GitHub links any unwrapped <img> to its own camo-proxied source, so an unlinked badge
        # dumps the visitor on a bare image. Every <img> in the README must sit inside <a href="...">.
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        unlinked = re.sub(r'<a\s[^>]*href="[^"]+"[^>]*>\s*<img\b[^>]*>\s*</a>', '', readme)
        self.assertEqual(re.findall(r'<img\b[^>]*>', unlinked), [], 'every <img> needs an <a href> around it')

    def test_refresh_routine_commits_only_the_readme_after_checks_and_honours_the_kill_switch(self):
        # 18 Nov 2026: the owner asked for the profile to follow new projects without retyping them.
        wf = (WF / 'refresh.yml').read_text(encoding='utf-8')
        run = wf.split('Commit only if it changed')[1]
        for step in ('ruff check .', 'unittest discover', '--check', 'AUTOMATION" = "off"'):
            self.assertLess(run.index(step), run.index('git -c user.name'), f'{step} must run before the commit')
        self.assertIn('-- README.md data/activity.json assets/previews', run)  # commits these and nothing else
        self.assertIn('contents: write   # commit README.md', wf)
        self.assertLess(run.index('previews.py "$RUNNER_TEMP/launchpad" --check'), run.index('git -c user.name'))  # P-08
        self.assertLess(wf.index('fetch_activity.py'), wf.index('build_readme.py "$RUNNER_TEMP/launchpad"\n'))
        self.assertLess(wf.index('previews.py "$RUNNER_TEMP/launchpad"\n'), wf.index('build_readme.py "$RUNNER_TEMP/launchpad"\n'))

    def test_new_project_without_a_preview_gets_no_broken_image(self):
        # P-03: a project merged into the launchpad before its preview image exists must not show a broken image.
        sys.path.insert(0, str(ROOT / 'tools'))
        import build_readme
        p = {'id': 'no-such-preview', 'name': 'New one', 'summary': 'Does a thing.', 'site': '',
             'repo': 'https://github.com/cyberdudeuk/no-such-preview', 'status': 'Experiment', 'licence': 'MIT'}
        cell = build_readme.card(p)
        self.assertNotIn('<img', cell)
        self.assertIn('New one', cell)
        self.assertIn('<img', build_readme.card(dict(p, id='dcat-ap-uk')))  # negative: an existing preview is still used

    def test_code_scanning_and_security_policy_exist(self):
        self.assertTrue((WF / 'codeql.yml').exists())
        self.assertIn('Report a vulnerability', (ROOT / 'SECURITY.md').read_text(encoding='utf-8'))


class Previews(unittest.TestCase):
    """P-08 and P-09: every listed project gets a current preview card, made safely from the data."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / 'tools'))
        import previews
        cls.pv = previews
        cls.p = {'id': 'demo', 'name': 'Demo <b>tool</b>', 'summary': 'One. Two.', 'status': 'Prototype', 'licence': 'MIT',
                 'site': 'https://cyberdudeuk.github.io/demo/', 'repo': 'https://github.com/cyberdudeuk/demo', 'category': 'ai'}
        cls.cat = {'label': 'AI governance', 'icon': 'shield'}

    def test_text_from_the_data_is_escaped(self):
        page = self.pv.page(self.p, self.cat, 'Prototype', {'shield': '<path d="M1 1"/>'}, 'sg.woff2')
        self.assertIn('Demo &lt;b&gt;tool&lt;/b&gt;', page)
        self.assertNotIn('<b>tool</b>', page)

    def test_summary_keeps_whole_sentences_and_always_the_first(self):
        self.assertEqual(self.pv.summary('Short. ' + 'x' * 300 + '.'), 'Short.')
        self.assertEqual(self.pv.summary('A' * 300 + '.'), 'A' * 300 + '.')

    def test_a_card_is_stale_when_missing_or_when_its_project_changes(self):
        import tempfile
        old_out, old_prints = self.pv.OUT, self.pv.PRINTS
        with tempfile.TemporaryDirectory() as t:
            self.pv.OUT, self.pv.PRINTS = Path(t), Path(t) / 'fingerprints.json'
            try:
                cats = {'ai': self.cat}
                self.assertEqual(self.pv.stale([self.p], cats), ['demo'])  # no card yet
                (Path(t) / 'demo.jpg').write_bytes(b'x')
                self.pv.PRINTS.write_text(json.dumps({'demo': self.pv.fingerprint(self.p, self.cat)}), encoding='utf-8')
                self.assertEqual(self.pv.stale([self.p], cats), [])  # current
                self.assertEqual(self.pv.stale([dict(self.p, licence='CC BY 4.0')], cats), ['demo'])  # P-09: data changed
            finally:
                self.pv.OUT, self.pv.PRINTS = old_out, old_prints

    def test_unsafe_ids_are_refused(self):
        self.assertIsNone(self.pv.ID.match('../evil'))
        self.assertIsNone(self.pv.ID.match('a/b'))
        self.assertIsNotNone(self.pv.ID.match('dam-policy-explorer'))

    def test_every_committed_card_is_current_with_the_launchpad(self):
        site = ROOT.parent / 'cyberdudeuk.github.io'
        if not (site / 'data' / 'projects.json').exists():
            self.skipTest('launchpad clone not alongside; the refresh routine runs previews.py --check against it')
        d = json.loads((site / 'data' / 'projects.json').read_text(encoding='utf-8'))
        self.assertEqual(self.pv.stale(d['projects'], {c['id']: c for c in d['categories']}), [])
        self.assertTrue({c['id'] for c in d['categories']} <= set(self.pv.PALETTE), 'every area has a colour')


if __name__ == '__main__':
    unittest.main()


sys.path.insert(0, str(ROOT / 'tools'))
import build_readme  # noqa: E402
import fetch_activity  # noqa: E402

FEED = """<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom">{}</feed>"""
ENTRY = '<entry><title>{t}</title><updated>{d}T10:00:00Z</updated><link href="https://github.com/x/{t}"/>' \
        '<author><name>{a}</name></author></entry>'


def feed(*rows):
    return FEED.format(''.join(ENTRY.format(t=t, d=d, a=a) for t, d, a in rows))


class Activity(unittest.TestCase):
    PROJECTS = [{'name': 'Plainspoken', 'repo': 'https://github.com/cyberdudeuk/plainspoken'},
                {'name': 'Other', 'repo': 'https://github.com/cyberdudeuk/other'}]

    def pages(self, url):
        return {'https://github.com/cyberdudeuk/plainspoken/releases.atom': feed(('Plainspoken 2.6.0', '2026-11-15', 'x')),
                'https://github.com/cyberdudeuk/plainspoken/commits.atom': feed(('Bump', '2026-11-19', 'dependabot[bot]'),
                                                                                ('Fix', '2026-11-18', 'cyberdudeuk')),
                'https://github.com/cyberdudeuk/other/releases.atom': feed(('v1.0.0', '2026-11-10', 'x')),
                'https://github.com/cyberdudeuk/other/commits.atom': feed(('Add', '2026-11-12', 'cyberdudeuk'))}[url]

    def test_last_change_is_by_a_person_and_releases_are_newest_first(self):
        a = fetch_activity.collect(self.PROJECTS, fetch=self.pages)
        self.assertEqual(a['last_change'], {'project': 'Plainspoken', 'date': '2026-11-18'})  # the bot's change ignored
        self.assertEqual([r['release'] for r in a['releases']], ['2.6.0', 'v1.0.0'])        # P-07: name not repeated

    def test_negative_a_failing_feed_is_skipped_not_fatal(self):
        def flaky(url):
            if 'other' in url:
                raise OSError('timeout')
            return self.pages(url)
        a = fetch_activity.collect(self.PROJECTS, fetch=flaky)
        self.assertEqual(len(a['releases']), 1)
        self.assertTrue(a['failed'])

    def test_negative_unsafe_inputs_are_refused(self):
        with self.assertRaises(ValueError):
            fetch_activity.get('https://evil.example/cyberdudeuk/x')       # only github.com/cyberdudeuk is fetched
        with self.assertRaises(ValueError):
            list(fetch_activity.entries('<!DOCTYPE x [<!ENTITY a "b">]><feed/>'))  # no DOCTYPE, so no entity tricks
        bad = fetch_activity.collect([{'name': 'Bad', 'repo': 'https://github.com/cyberdudeuk/../../x?y'}],
                                     fetch=lambda u: self.fail('fetched a bad name'))
        self.assertTrue(bad['failed'])


class Readme(unittest.TestCase):
    README = (ROOT / 'README.md').read_text(encoding='utf-8')

    def test_colophon_shows_the_last_change_not_the_register_date(self):
        # P-05
        act = json.loads((ROOT / 'data' / 'activity.json').read_text(encoding='utf-8'))
        self.assertIn(f'last change {act["last_change"]["date"]}', self.README)
        self.assertNotRegex(self.README.split('<sub>Public Good Works')[-1], r'updated \d{4}')
        self.assertEqual(build_readme.colophon_date({'updated': '2026-11-15'}, {}), 'updated 2026-11-15')  # fallback

    def test_profile_links_notes_board_and_shows_whats_new(self):
        # P-06
        for url in (build_readme.NOTES, build_readme.FEED, build_readme.BOARD):
            self.assertIn(url, self.README)
        self.assertIn("## What's new", self.README)
        self.assertIn('## Start here', self.README)

