# Changelog

## 15 November 2026

- Checks run on every push and pull request: the Ruff linter (fails on any finding), the unit tests, and a check that
  `README.md` is exactly what `tools/build_readme.py` makes from the launchpad's data. CodeQL scans the Python and the
  workflows; Dependabot keeps the pinned actions current. Security policy and contributing guide added. Part of applying
  the secure development standard to every project.
- Profile page created: banner, project cards with social previews, QR code and barcode colophon.
