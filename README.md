# myresearchpy

[![Tests](https://github.com/your-org/myresearchpy/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/your-org/myresearchpy/actions/workflows/tests.yml)
[![Documentation](https://github.com/your-org/myresearchpy/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/your-org/myresearchpy/actions/workflows/docs.yml)
[![Template check](https://github.com/your-org/myresearchpy/actions/workflows/template-check.yml/badge.svg?branch=main)](https://github.com/your-org/myresearchpy/actions/workflows/template-check.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)

The three status badges track the `tests`, `docs` and `template-check` workflows
and show `unknown` until you push to a repository of your own. **Template check
will report failure until you finish the migration** — that is the intended
signal, not a defect. See [Adapting this template](#adapting-this-template).

<!--intro-start-->

A template for **theoretical research software in Python**, organised around the
[FAIR4RS](https://fair4rs.org) and [FAIR-CURE](https://doi.org/10.15497/RDA00068)
guidelines. Replace `myresearchpy` with your package name, fill in the modules
under `src/`, and you have a publishable research codebase from day one.

The template ships working reference implementations rather than empty stubs, so
the test suite and the built documentation both start out green.

<!--intro-end-->

## Why this structure

Research code rots for predictable reasons: undocumented assumptions, unpinned
dependencies, and results that cannot be traced back to the inputs that produced
them. This template attacks each one directly.

| Problem | Countermeasure in this template |
| --- | --- |
| "It worked on my machine" | pixi environments and a committed `pixi.lock` |
| Assumptions live in someone's head | numpydoc docstrings feeding the API reference |
| Numbers nobody can reproduce | Tests asserting against *exact* analytic results |
| Provenance lost | Seeding plus an environment report utility |
| Docs rot silently | CI builds docs and fails on Sphinx warnings |
| Reviewer cannot rebuild | BSD-3 license, CITATION file, `CONTRIBUTING` guide |

## Quick start

Requires [pixi](https://pixi.sh) and nothing else.

```bash
pixi install          # resolve dependencies into .pixi/
pixi run test         # run the test suite
pixi run docs         # build HTML docs into docs/_build/html
pixi shell            # interactive shell with every dependency present
```

Individual environments:

```bash
pixi run -e test test          # tests only
pixi run -e docs docs-strict   # docs, failing on any warning
pixi run -e dev lint           # ruff
pixi run -e py310 test         # tests pinned to Python 3.10
```

## Environments

pixi features compose into named environments, so CI and local development use
the same dependency specifications.

| Environment | Features | Contents |
| --- | --- | --- |
| `default` | `test`, `docs`, `dev` | everything, for development |
| `test` | `test` | runtime + pytest, minimal |
| `docs` | `docs` | Sphinx toolchain |
| `dev` | `test`, `docs`, `dev` | same as default, for CI linting |
| `py310` … `py313` | `py31x`, `test` | pinned interpreter, for the CI matrix |

The `py31x` environments pin an exact Python minor version, so the CI matrix
really does exercise 3.10 through 3.13 rather than always resolving to the
newest version allowed by `requires-python`.

## Example

```python
from myresearchpy import harmonic_oscillator_energy, variational_energy_hydrogen

# Exact spectrum: E_n = ħω(n + 1/2)
harmonic_oscillator_energy([0, 1, 2])
# array([0.5, 1.5, 2.5])

# Variational upper bound on the hydrogen ground state (-0.5 Ha exact)
variational_energy_hydrogen(grid_points=2000)
# -0.49980...
```

## Layout

```
myresearchpy/
├── pyproject.toml            # metadata, pixi environments, tooling config
├── pixi.lock                 # exact dependency resolution (committed)
├── LICENSE                   # BSD-3-Clause
├── CITATION.cff              # machine-readable citation metadata
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── src/
│   └── myresearchpy/
│       ├── __init__.py       # curated public API
│       ├── __version__.py    # single source of version truth
│       ├── energy.py         # analytical spectra, variational estimates
│       ├── linalg.py         # generalised eigenproblems
│       └── utils.py          # seeding, provenance
├── tests/                    # mirrors src/, pytest
│   └── conftest.py
├── docs/                     # MyST Markdown + Sphinx
│   ├── conf.py
│   ├── index.md
│   ├── theory.md             # derivations behind the code
│   ├── contributing.md
│   ├── tools.md              # the software tools used, with documentation
│   ├── changelog.md
│   └── api/                  # autodoc pages
├── scripts/
│   └── check_template.py     # verifies the migration is complete
└── .github/workflows/        # tests, docs, lint, template check, release
```

## Documentation

Build locally with `pixi run docs`. The API reference is generated from the
docstrings via numpydoc, so it cannot drift from the source. `docs/theory.md`
holds the derivations, which is the part reviewers most often ask for and
contributors most often skip.

In CI the docs workflow publishes to GitHub Pages on every push to `main` and
enforces a warning-free build (`-W`), so a documentation regression is caught
rather than shipped.

## Software tools

The complete list of tooling, with links to the upstream documentation, is in
[Software tools](docs/tools.md). In short: pixi for environments, pytest and
ruff for testing and linting, Sphinx for documentation, and GitHub Actions with
GitHub Pages for CI and hosting.

## Continuous integration

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| `tests.yml` | push, PR | tests on Linux/macOS/Windows, Python 3.10–3.13 |
| `docs.yml` | push, PR touching docs | warning-free Sphinx build, deploy to Pages |
| `lint.yml` | push, PR | `ruff check` and format verification |
| `template-check.yml` | push, PR | no template placeholders or metadata drift left |
| `release.yml` | version tags | version/tag consistency check, tests, PyPI publish |

## Adapting this template

Two paths, depending on where your code already lives:

- [**New project**](#new-project) — start from the template, then fill it in.
- [**Existing codebase**](#existing-codebase) — wrap code you already have,
  possibly a directory that has never been under version control.

Both share the same end state. If you are adopting existing code, work through
that checklist; it is longer and starts with GitHub setup, which you will not
need otherwise.

### New project

1. Create the repository from this template (**Use this template**, or
   `gh repo create --template`).
2. Rename the package: `src/myresearchpy/` and the `name` fields in
   `pyproject.toml`.
3. Set the version in `src/myresearchpy/__version__.py`.
4. Replace the placeholder modules, keeping docstrings complete.
5. Update the URLs in `pyproject.toml`, `CITATION.cff` and `docs/conf.py`.
6. Update the badge URLs at the top of this README to your repository slug. They
   are the one place the repository name appears, so the status badges stay
   `unknown` until you do.
7. Point `.github/workflows/docs.yml` at your GitHub Pages environment.
8. Delete the reference implementations and their tests once you have real
   equivalents.
9. Run `pixi run check-template` until it passes.

`scripts/check_template.py` verifies the rename reached every required location
and that no placeholder survives. It exits non-zero while anything is left, which
is why the *Template check* workflow is red on an unmodified copy of this
template. See [Migration checklist](docs/contributing.md#migration-checklist)
for what each check covers.

### Existing codebase

Assumes your code is a local directory with **no** `.git/`, no `pyproject.toml`,
and no GitHub remote. Work top to bottom; the early steps change what later ones
mean.

#### 1. Decide on a license before you publish anything

Do this first, because it determines what the GitHub repository is created with
and it constrains everything you do afterwards.

Code with no license is **not** open source. Under copyright law, absent an
explicit grant, the default is exclusive rights reserved: nobody else may legally
copy, modify or redistribute it, which is incompatible with the FAIR principle
of *Accessible*. Publishing first and licensing later leaves a window in which
others may have already committed code they cannot safely use.

Check these three things before choosing:

- **Your employer or institution.** Employment contracts and staff rules often
  assign copyright to the institution, or require approval to release code.
  For academic and government labs this is common, so check before you assume
  the choice is yours.
- **Your funder or grant.** Some funders require an explicit license and a
  statement of provenance in the repository.
- **Collaborators and co-authors.** If the work is jointly owned, agree on a
  license and copyright line with your co-authors. A mismatched expectation here
  is awkward to unwind later.

Then pick a license. For research software intended to be reused, a permissive
license is the usual right answer: it maximises the chance of reuse, which is
the point of the exercise. You can also **not** license, and keep the code
private — a deliberate option, not an oversight.

#### 2. Choose the license on GitHub

GitHub hosts a curated chooser at <https://choosealicense.com>, and a
**Licenses** setting in each repository's **Settings**. The template ships
BSD-3-Clause, which is a reasonable default for scientific code.

Two ways to apply it:

**Via the web interface** — create the repository, then go to **Add file →
Create new file**, type `LICENSE` in the filename box, and GitHub offers a
license template. Pick one and commit. This is the path to follow if you are
starting from scratch.

**From the local command line** — if your code is already on disk (the case
here), you have no GitHub repository yet, so you cannot use that interface.
Pick the license first:

1. Browse <https://choosealicense.com> and read the license text in full. Read
   the actual license, not just the summary — the summary hides detail.
2. Save the text as `LICENSE` in the root of your code directory, replacing this
   template's copy.
3. Fill in the copyright line with the legal name of the copyright holder and
   the year. Use the individual or the institution, per your answer in step 1.
   `Copyright (c) 2026 Your Name` is a placeholder, not a default.
4. Set the SPDX identifier in `pyproject.toml` so tooling agrees with the file:

   ```toml
   license = { text = "BSD-3-Clause" }
   classifiers = ["License :: OSI Approved :: BSD License"]
   ```

   The SPDX id must match the file you saved, or package metadata will
   contradict the license text.

Common choices for research software:

| License | Character | Notes |
| --- | --- | --- |
| BSD-3-Clause | Permissive | Template default. Adds a no-endorsement clause over BSD-2. |
| MIT | Permissive | Shortest and most permissive; no explicit patent grant. |
| Apache-2.0 | Permissive | Explicit patent grant; longer. Common in industry. |
| MPL-2.0 | Weak copyleft | Changes to MPL-covered files stay open; can be combined with proprietary code. |
| GPL-3.0 | Strong copyleft | Derived works must also be GPL. Strongest guarantee of reuse. |

Choose from your institution's approved list if it has one — some funders and
universities restrict what you may apply.

Check your dependencies too. Permissive projects can still be affected by the
licenses of what they import; the three here (NumPy, SciPy, SymPy) are all
BSD-3-Clause.

#### 3. Make the directory a git repository

```bash
cd path/to/your/code
git init
git add .
git commit -m "Initial import of <project name>"
```

Commit before adding the template if you want the original state as a separate
commit. That first snapshot is your only record of what the code looked like
before cleanup, and it makes the migration diff reviewable.

Check `.gitignore` **before** committing. Research directories habitually hold
data files, editor backups and compiled output, and the first commit is the one
that goes into history permanently. Rewrite history with `git filter-repo` if
you commit something large or secret by mistake.

#### 4. Add the template without losing your code

Copy in the template's scaffolding — `pyproject.toml`, `pixi.lock`, `docs/`,
`tests/`, `.github/`, `LICENSE`, `CITATION.cff`, `CHANGELOG.md`,
`CODE_OF_CONDUCT.md`, `.gitignore`, `.pre-commit-config.yaml` — and keep your
existing source.

Then resolve the collision deliberately. Both your code and the template want
`tests/` and `docs/`. The template's reference implementations under
`src/myresearchpy/` are examples, not something to preserve; move your real
modules into `src/<yourpackage>/` and delete or repurpose theirs. Move your own
tests into `tests/` alongside the template's and delete any that only covered
the reference implementations.

If your existing code predates packaging and imports by directory name rather
than as an installed package, moving it under `src/` will break those imports.
Fix them to relative or absolute package imports, then confirm
`pixi run test` passes before continuing.

#### 5. Declare dependencies and get a green run

Replace the dependency lists in `pyproject.toml` with what your code actually
imports. This is the step people skip, and it is the one that determines whether
the package is reproducible.

List what is genuinely required. A dependency you did not check for may be
transitively available today and absent after a fresh resolve, which reproduces
as a confusing `ImportError` on someone else's machine.

Then delete the template's placeholder modules and their tests, and get a real
green run:

```bash
pixi install
pixi run test        # must pass before anything else
pixi run lint        # ruff; fix or relax the rules deliberately
pixi run docs        # confirm autodoc picks up your modules
```

Update `docs/api/` to `automodule` your modules instead of the reference ones.

#### 6. Rename and fill in the metadata

Rename the package directory and every `myresearchpy` reference in
`pyproject.toml`, `CITATION.cff`, `docs/conf.py`, and the README. Set the version
in `src/<yourpackage>/__version__.py` — `pyproject.toml` reads it from there, so
there is one place to change.

Update `CHANGELOG.md` with an entry describing the initial import, and fill in
`CITATION.cff` so your work is citable. Archive a DOI via Zenodo once the
repository is public; it is what makes a result referenceable in perpetuity.

#### 7. Publish and verify

```bash
gh repo create <name> --public --source=. --remote=origin --push
```

Or create the empty repository on GitHub, then `git remote add origin` and
`git push -u origin main`.

Then check the things only CI can tell you:

- **Actions** — confirm the test, lint and docs workflows all passed. The docs
  job needs a `github-pages` environment; create it under **Settings →
  Environments** if the deploy step fails.
- **Pages** — the docs workflow deploys on push to `main`; the live URL appears
  in the job summary.
- **Secret scanning** — confirm no credentials or data files reached the public
  repository. This is irreversible once public.

Finally, add contributors (`Settings → Collaborators`) and set up branch
protection on `main` requiring the test workflow to pass.

### Checklist

- [ ] Copyright holder confirmed with employer/institution
- [ ] License chosen and `LICENSE` updated with the correct holder and year
- [ ] SPDX identifier in `pyproject.toml` matches the license file
- [ ] Dependencies' licenses checked
- [ ] `.gitignore` reviewed; no data, secrets or large files
- [ ] `git init` and first commit made
- [ ] Template files added; `tests/` and `docs/` collisions resolved
- [ ] Source moved under `src/<yourpackage>/`; imports fixed
- [ ] Dependencies declared from actual imports
- [ ] Reference implementations and their tests removed
- [ ] `pixi run test` passes
- [ ] `pixi run lint` clean
- [ ] `pixi run docs` builds; `docs/api/` updated
- [ ] Package renamed throughout; version set in `__version__.py`
- [ ] `CHANGELOG.md` and `CITATION.cff` filled in
- [ ] `pixi run check-template` reports every check passed
- [ ] Badge URLs in this README updated to your repository slug
- [ ] GitHub repository created and pushed
- [ ] All workflows green; `github-pages` environment configured
- [ ] Zenodo DOI minted
- [ ] Branch protection and collaborators configured
- [ ] Verified no secrets or unpublished data are public

## Citing

See `CITATION.cff`. Cite the specific version you used; a result without a
version cannot be reproduced.

## License

BSD-3-Clause. See [LICENSE](LICENSE).

Adopting this template does not settle the license for your project. Choose one
explicitly before publishing — see
[step 1](#1-decide-on-a-license-before-you-publish-anything).

## References

- Barker et al., *FAIR4RS v1.0*, Research Software Policy Institute, 2022.
  <https://doi.org/10.5281/zenodo.6623556>
- Chue Hong et al., *FAIR-CURE*, Research Data Policy, 2022.
  <https://doi.org/10.15497/RDA00068>
- de Berg, Feringa, Gini, *Reusable research software: a FAIR software approach*, 2020. <https://doi.org/10.1007/s10618-020-00761-8>
- GitHub, *Choose an open source license*, <https://choosealicense.com>
  (accessed when selecting a license).
