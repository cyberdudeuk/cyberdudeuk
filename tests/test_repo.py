"""Repository checks for the profile page (secure development standard, 15 Nov 2026).

P-01: the repository had no CI at all, so a lint finding or a stale README could merge unnoticed.
P-02: the "projects" badge was a bare <img>, so clicking it on the profile opened the raw SVG on
      camo.githubusercontent.com instead of going anywhere useful (18 Nov 2026).
P-03: a project newly merged into the launchpad has no preview image yet; the README must not show a broken image.
"""
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
        self.assertIn('-- README.md', run)                 # commits README.md and nothing else
        self.assertIn('contents: write   # commit README.md', wf)

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


if __name__ == '__main__':
    unittest.main()
