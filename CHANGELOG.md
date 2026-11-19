# Changelog


## 19 November 2026: a live front page

- **Start here** names one flagship to try first: the GitHub Repos Asset Catalogue (set by FLAGSHIP in
  tools/build_readme.py).
- **What's new** shows the latest release of each project, the latest notes from the launchpad, and a link to the
  Public Good Works project board with its weekly status update. tools/fetch_activity.py reads each project's public
  release and commit feeds into data/activity.json; the daily refresh commits it with README.md.
- The colophon now shows the last change by a person to any project, not the register's own date, which had made the
  page look stale (P-05). Badges now link LinkedIn, the notes and the board too (P-06). Release names no longer repeat
  the project name (P-07).

## 18 November 2026: DEV Community profile linked

- A DEV badge (https://dev.to/cyberdudeuk) now sits beside the ORCID badge, matching the DEV link added to the
  GitHub sidebar. A new check fails if the README stops linking any public profile the sidebar shows (defect P-04).

## 18 November 2026: the profile follows the launchpad by itself

- A daily refresh routine rebuilds README.md from the launchpad's project list and, if it changed, commits it after
  the linter, the tests and the README check pass. It commits README.md and nothing else; the AUTOMATION variable
  set to "off" stops it. New projects reach the profile once a person merges them on the launchpad.
- A project with no preview image yet is shown as a linked name and summary, never a broken image (P-03).

## 18 November 2026

- The "projects" badge now links to the Projects section, and the colophon barcode links to the launchpad. Both were bare
  images, so clicking either opened the raw SVG on GitHub's image proxy. A new check fails if any image in the README is
  not inside a link (defect P-02).
- Python bytecode (`__pycache__`) is no longer tracked; a `.gitignore` keeps it out.

## 15 November 2026

- Checks run on every push and pull request: the Ruff linter (fails on any finding), the unit tests, and a check that
  `README.md` is exactly what `tools/build_readme.py` makes from the launchpad's data. CodeQL scans the Python and the
  workflows; Dependabot keeps the pinned actions current. Security policy and contributing guide added. Part of applying
  the secure development standard to every project.
- Profile page created: banner, project cards with social previews, QR code and barcode colophon.
