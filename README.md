# Numpy project template
[![Python 3.11](https://img.shields.io/badge/python-3.11+-blue.svg?logo=python&logoColor=cccccc)](https://www.python.org/downloads/) 
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm-project.org)
[![documentation](https://img.shields.io/badge/docs-mkdocs%20material-blue.svg?style=flat)](https://squidfunk.github.io/mkdocs-material/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![Code Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen?logo=codecov)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)
[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json)](https://github.com/copier-org/copier)

Construct a `numpy`-based Python project from scratch for scientific computing and research.

## Features

- [Numpy](https://numpy.org/) a basic installation of the holy trifecta :dove: of `numpy, matplotlib, scipy`.
- [PDM](https://pdm-project.org) for dependency, virtualenv, and package management.
- [Mkdocs material](https://squidfunk.github.io/mkdocs-material/) for simple, clean, automated, online code documentation.
- [pre-commit](https://github.com/pre-commit/pre-commit) with [ruff](https://github.com/astral-sh/ruff) integration for code linting and formatting.
- [pytest](https://docs.pytest.org/en/stable/index.html#) with [coverage](https://pytest-cov.readthedocs.io/en/latest/) for regression testing and code coverage.
- [Commitizen](https://github.com/commitizen-tools/commitizen) with [conventional commits](https://conventionalcommits.org) for automatic versioning and changelogs.
- [Copier](https://github.com/copier-org/copier) for continuously updating project from this original template.
- [Github actions](https://docs.github.com/en/actions) for automated, build, test, and deployment.

## Quickstart
```shell
# Obviously, have python and git installed
pip install --user pdm
pdm self add copier copier-templates-extensions

cd path/to/project
pdm init --copier gh:eckelsjd/copier-numpy --trust
```
That's it! Follow the questionnaire and then your `numpy`-based scientific computing project is ready to go. 

All extra arguments are passed to `copier copy` (you're also welcome to just use `copier` directly).

## Publishing on PyPI
Follow [this tutorial](https://docs.pypi.org/trusted-publishers/) to enable trusted publishing with Github actions. Then, do:
```shell
pdm bump
```
That's it! Your package will automatically deploy to PyPI and GitHub with a correctly-versioned `vX.X.X` tag.

## See similar
- [Scientific Python library development](https://github.com/scientific-python/cookie)
- [Copier-pdm](https://github.com/pawamoy/copier-pdm) and the similar [pdm-project](https://github.com/pdm-project/copier-pdm) version
- [Serious scaffolding](https://github.com/serious-scaffold/ss-python) for Python projects
- [LINCC framework](https://github.com/lincc-frameworks/python-project-template) for Python projects by the University of Washington
- [copier-pylib](https://github.com/astrojuanlu/copier-pylib) for pure Python projects
