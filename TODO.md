# Documentation
- [x] Come up with generic template for mkdocs-material
- [x] Automate generation of API reference pages from src directory
- [x] Include git committers, last edited date, things at bottom of each page
- [x] test coverage plugin

# Testing
- [x] Come up with generic template for pytest
- [x] Automate coverage badge
- [xx] Look into nox/tox local automated testing over python versions and in github runners
- [x] pre-commit hook to ruff check and run pytest

General workflow will be:
1. pre-commit will lint, check for sensitive data, check for an up to date `pytest` run, and check that commit message is formatted correctly. Will block if lint or tests failed. README coverage badge automatically updated after `pytest`.
2. Then the user manually fixes lint/test errors. Can also use `ruff check --fix` to automatically fix lint errors. No formatting is forced at this time but would be easy with `ruff format`.
3. On pull request to main, a GHA will run all the `pytest` and `ruff checks` again on multiple versions/platforms (would be nice to have a cache to skip new install each time).
4. On commit to main, another test-coverage is generated and read into automatic gh-pages deploy for coverage report.
5. (new tag/version/release/changelog released on manual command, but all generated automatically from commit history since last release. Should treat `0.x.x` as alpha with no breaking changes possible.)

# CI/CD
- [ ] Look into build caches for github runners
- [x] Look into pre-commit and ruff for automatic linting
- [ ] Look into github api to automatically setup remote repo settings from a script/cli
- [x] Look into towncrier/commitizen for automatic changelogs
- [x] Look into best ways to bump __version__ and vcs tag in a release. Auto generates changelogs and appropriate version based on commit messages.
- [ ] Look into dependabot

# Copier
- [x] Run an initialization script to install prod and git init and push to new remote repo.
- [x] Newly copied repo should install pre-commit and setup
- [ ] Migrate amisc/uqtils to this template
