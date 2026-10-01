# Contributing

Thank you for considering a contribution. This template follows
[FAIR4RS](https://fair4rs.org) and
[FAIR-CURE](https://doi.org/10.15497/RDA00068) guidelines, and contributions
are expected to preserve those properties.

## Getting started

The repository ships [pixi](https://pixi.sh) environments, so there is no
manual dependency installation step.

```bash
pixi install          # resolve and populate .pixi/
pixi run test         # run the test suite
pixi run docs         # build the HTML documentation
pixi shell            # interactive shell with every dependency
```

Individual environments are also available:

```bash
pixi run -e test test
pixi run -e docs docs
pixi run -e dev lint
```

## Development workflow

1. Open an issue describing the bug fix or feature first.
2. Create a branch: `git checkout -b topic-short-description`.
3. Make your change, with tests that fail before it and pass after.
4. Run `pixi run test` and `pixi run lint`.
5. Open a pull request referencing the issue with `Closes #<n>`.

## What we ask of new code

**Correctness.** Every new function needs a docstring with Parameters,
Returns and Raises sections in numpydoc format. The API reference is generated
from those docstrings, so they are user-facing documentation, not comments.

**Validation.** Check preconditions at the function boundary and raise
`ValueError` with a message that names the offending value. Fail loudly rather
than silently returning a wrong number.

**Reference tests.** Where an exact analytical result exists, assert against it
rather than against a previously recorded output. Self-validating tests survive
refactoring; golden-file comparisons do not.

**Physical plausibility.** Include at least one test per function that asserts a
qualitative property: a bound, a scaling law, an order-of-magnitude range, or a
convergence trend. These catch modelling errors that unit tests miss.

**Reproducibility.** Seed random numbers through `myresearchpy.set_seed`. Never
rely on uninitialised global state.

**Provenance.** When a function is stochastic or depends on truncation, mention
it in the docstring `Notes` section so the error can be bounded.

## Tests

Tests live in `tests/` and mirror the package layout. Keep unit tests fast;
mark expensive ones with `@pytest.mark.slow`. The suite runs with
`filterwarnings = ["error"]`, so any warning becomes a failure.

```bash
pixi run test                  # everything
pixi run test-cov              # with coverage report
pixi run test tests/test_energy.py::test_ground_state_energy_is_half_hbar_omega
```

## Documentation

Documentation lives in `docs/` as MyST Markdown. Prose goes in `.md` files;
API pages use `automodule` directives and are written by hand so that
`__init__` does not pull in unrelated docstrings. Mathematical expressions use
`$...$` inline and `$$...$$` display delimiters, rendered by MathJax.

```bash
pixi run docs-live              # rebuild on save, with live reload
```

## Code style

Formatting and linting are handled by `ruff`, configured in
`pyproject.toml`. NumPy-style docstring rules (`D`) are enforced. Run
`pixi run format-fix` before committing.

## Licensing

By contributing you agree that your contribution is licensed under the
BSD-3-Clause license of this repository. See [License](license.md) for how that
license was selected.

Note that adopting this template does not license your own project: choose a
license explicitly before publishing. If you are contributing to a project that
is not yet licensed, say so in the pull request rather than assuming one has
been chosen.

Cite the package as `myresearchpy` (replace with your name) with the version
from `src/myresearchpy/__version__.py`, which is also where `pyproject.toml`
reads its version from — update both together.

## Migration checklist

This template is a starting point, not a finished project. Before your first
release, every placeholder must be replaced with your own values.
`scripts/check_template.py` verifies that for you, and the *Template check*
workflow runs it on every push and pull request. That workflow fails on the
unmodified template by design; it goes green once the migration is complete.

```bash
pixi run check-template
```

The checker never modifies files and has no third-party dependencies.

| Check | Verifies |
| --- | --- |
| `placeholders` | No template package name, author, email, organisation, ORCID or DOI placeholder survives anywhere in the tracked tree. |
| `package-name` | The name in `pyproject.toml` matches `src/<name>/`, `docs/conf.py` and `CITATION.cff`. |
| `version` | `pyproject.toml`, `src/<name>/__version__.py` and `CITATION.cff` report the same version. |
| `api-docs` | Every public module has an `automodule` page in `docs/api/`, and every page points at a module that exists. |
| `license` | The SPDX identifier matches the `LICENSE` text, and the copyright line names a real person. |

Run one check at a time while migrating, and add `--verbose` for remediation
hints:

```bash
pixi run python scripts/check_template.py --only license --verbose
```

The DOI placeholder can only be resolved once your Zenodo DOI has been minted.
Everything else must be settled before you publish.
