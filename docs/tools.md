# Software tools

Every tool below is already configured in this repository. Nothing here needs to
be installed by hand: pixi resolves and populates `.pixi/` from `pixi.lock`, so
`pixi run <task>` works on a fresh clone.

The list is split by role. Tools in the first group are part of the paper or
project itself; the rest support the surrounding work of building, testing,
documenting and releasing it.

## Core dependencies

These are declared in `[project].dependencies` and are needed to *use* the
package.

- [**NumPy**](https://numpy.org/doc/stable/) — the array types and linear algebra
  the package is written against.
- [**SciPy**](https://docs.scipy.org/doc/scipy/) — numerical routines beyond what
  NumPy provides, such as special functions and optimisation.
- [**SymPy**](https://docs.sympy.org/latest/index.html) — symbolic manipulation,
  used to derive closed forms in the theory documentation.
- [**tomli**](https://pypi.org/project/tomli/) — TOML parser, installed only on
  Python 3.10 where `tomllib` is not yet stdlib. Used by the template checker to
  read `pyproject.toml`; the package itself does not import it.

## Testing and quality

- [**pytest**](https://docs.pytest.org/en/stable/) — test runner and fixtures.
  Configured in `[tool.pytest.ini_options]`, with `filterwarnings = ["error"]` so
  any warning becomes a failure.
- [**pytest-cov**](https://pytest-cov.readthedocs.io/en/stable/) — coverage
  reporting. Branch coverage is enabled and `pixi run test-cov` writes
  `coverage.xml` for the CI artifact.
- [**ruff**](https://docs.astral.sh/ruff/) — linter and formatter. Runs in place
  of a separate `flake8`/`black` pair; NumPy-style docstring rules (`D`) are
  enforced.
- [**coverage.py**](https://coverage.readthedocs.io/en/latest/) — the measurement
  engine behind `pytest-cov`.
- [**mypy**](https://mypy.readthedocs.io/en/stable/) — static type checking of
  `src/`, run through pre-commit.

## Documentation

- [**Sphinx**](https://www.sphinx-doc.org/en/master/) — documentation generator.
- [**MyST-Parser**](https://myst-parser.readthedocs.io/en/stable/) — lets the
  prose live in Markdown `.md` files instead of reStructuredText.
- [**numpydoc**](https://numpydoc.readthedocs.io/en/latest/) — renders docstrings
  into the API reference, honouring the `Parameters`/`Returns`/`Raises`
  convention the code style asks for.
- [**sphinx-book-theme**](https://sphinx-book-theme.readthedocs.io/en/latest/) —
  the documentation theme.
- [**sphinx-copybutton**](https://sphinx-copybutton.readthedocs.io/en/latest/) —
  renders the copy-to-clipboard buttons on code blocks.
- [**MathJax**](https://www.mathjax.org/) — renders the `$...$` and `$$...$$`
  mathematics in the theory pages. Loaded by Sphinx, so there is no separate
  dependency to install.

## Environment and dependency management

- [**pixi**](https://pixi.sh/latest/) — creates and manages the virtual
  environments, and runs the tasks behind `pixi run test`, `pixi run docs` and
  `pixi run lint`. Environments are declared per Python minor version in
  `pyproject.toml`; `pixi.lock` records the exact resolution and is committed.
- [**hatchling**](https://hatch.pypa.io/latest/) — the build backend that produces
  the wheel and source distribution. Configured in `[build-system]`.

## Continuous integration and publishing

- [**GitHub Actions**](https://docs.github.com/en/actions) — runs every workflow
  in `.github/workflows/`.
- [**actions/checkout**](https://github.com/actions/checkout) — checks out the
  repository, including the tags the release workflow verifies version against.
- [**prefix-dev/setup-pixi**](https://github.com/prefix-dev/setup-pixi) —
  installs the pixi environment in CI, with caching keyed on `pixi.lock`. Use its
  `environments` input to select which environment to install.
- [**actions/upload-artifact**](https://github.com/actions/upload-artifact) —
  retains `coverage.xml` from the test run for later inspection.
- [**pypa/gh-action-pypi-publish**](https://github.com/pypa/gh-action-pypi-publish)
  — uploads the built distribution to PyPI, using a trusted publishing token so no
  long-lived API key is stored in the repository.
- [**GitHub Pages**](https://docs.github.com/en/pages) — hosts the built HTML
  documentation, configured in `docs.yml` with `configure-pages`,
  `upload-pages-artifact` and `deploy-pages`.
- [**Zenodo**](https://zenodo.org/) — mints the DOI recorded in `CITATION.cff`.
  This is a manual step: a DOI cannot exist until the release it identifies has
  been archived, so the template checker expects the placeholder to still be
  there until you replace it.
- [**CFFConverter / citation-file-format**](https://citation-file-format.github.io/)
  — the `CITATION.cff` schema. Metadata is written by hand in that format rather
  than through a tool, but the schema documentation is the reference when filling
  it in.

## Version control and repository setup

- [**Git**](https://git-scm.com/doc) — version control.
- [**pre-commit**](https://pre-commit.com/) — runs `trailing-whitespace`,
  `check-yaml`, `check-toml`, `ruff`, `ruff-format` and `mypy` at commit time.
  Installed with `pixi run -e dev precommit-install`.