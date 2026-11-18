"""Repository checks for the profile page (secure development standard, 15 Nov 2026).

P-01: the repository had no CI at all, so a lint finding or a stale README could merge unnoticed.
P-02: the "projects" badge was a bare <img>, so clicking it on the profile opened the raw SVG on
      camo.githubusercontent.com instead of going anywhere useful (18 Nov 2026).
"""
import re
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

    def test_code_scanning_and_security_policy_exist(self):
        self.assertTrue((WF / 'codeql.yml').exists())
        self.assertIn('Report a vulnerability', (ROOT / 'SECURITY.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
