# Documentation
- [x] Come up with generic template for mkdocs-material
- [x] Automate generation of API reference pages from src directory
- [x] Include git committers, last edited date, things at bottom of each page
- [x] test coverage plugin
- [ ] versioned documentation
- [ ] including interactive python or jupyter in mkdocs site

# Testing
- [x] Come up with generic template for pytest
- [x] Automate coverage badge
- [xx] Look into nox/tox local automated testing over python versions -- can just do this with test matrix in Github actions for PRs only (these additionally can test over multiple platforms, and its automated)
- [x] pre-commit hook to ruff check and check pytest status

# CI/CD
- [ ] Look into build caches for github runners. Cache htmlcov from PR test job and use in build docs for coverage report.
- [x] Look into pre-commit and ruff for automatic linting
- [x] Look into github api to automatically setup remote repo settings from a script/cli
- [x] Look into towncrier/commitizen for automatic changelogs
- [x] Look into best ways to bump version and vcs tag in a release. Auto generates changelogs and appropriate version based on commit messages.
- [xx] Look into dependabot -- not needed right now

# Copier
- [x] Run an initialization script to install, git init, and push to new remote repo.
- [x] Newly copied repo should install pre-commit and setup
- [x] Add license file automatically
- [ ] Option in `setup_github.py` to detect and change who is logged in to gh CLI (or exit)
- [ ] Migrate amisc/uqtils to this template and check the usage of `copier update`.
- [x] Make sure this all works in linux too (works on ubuntu at least)

# General workflow
1. User should be running `pdm test` and `pdm lint` to make sure their code works and is up to snuff.
1. `pre-commit` will lint, check for sensitive data, check for an up to date `pytest` run, etc. and check that commit message is formatted correctly. Will block if lint or tests failed. README coverage badge automatically updated after `pytest`.
1. Then the user manually fixes lint/test errors. Can also use `ruff check --fix` to automatically fix lint errors. No formatting is forced at this time but would be easy with `ruff format`.
1. On pull request to main, a GHA will run all the `pytest` and `ruff checks` again on multiple versions/platforms.
1. On commit to main, another test-coverage is generated and read into automatic gh-pages deploy for coverage report.
1. With a manual `pdm bump`, a new tag/version/release/changelog/build are generated from commit history and released. Uses `commitizen` under the hood to manage this.
