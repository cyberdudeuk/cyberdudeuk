# Contributing

`README.md` is built, not edited by hand: `python tools/build_readme.py <path to a clone of cyberdudeuk.github.io>`
reads the launchpad's `data/projects.json` and writes it. To change what a project card says, change the launchpad's data.

Every pull request runs the checks in `.github/workflows/checks.yml`: the Ruff linter (any finding fails), the unit
tests, and a check that `README.md` matches what the script makes. Every defect fixed gets a test that fails without
the fix. Report security problems privately (see SECURITY.md).
