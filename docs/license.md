# License

```{literalinclude} ../LICENSE
:language: text
```

## Choosing a license

This template ships BSD-3-Clause, which is a sensible default for research
software intended to be reused. It is a placeholder, not a decision: adopting
the template does not license your code.

Code with no license is not open source. Absent an explicit grant, copyright law
leaves the author with exclusive rights, so nobody else may legally copy, modify
or redistribute it. That is incompatible with the *Accessible* element of FAIR.

GitHub maintains a curated chooser at <https://choosealicense.com>, and a
**Licenses** setting under repository **Settings**. In a repository that already
exists, **Add file → Create new file** offers license templates when you name
the file `LICENSE`.

For research software, a permissive license is usually right, since it maximises
the chance of reuse. Keeping the code unlicensed and private is also a
legitimate choice, but make it a deliberate one.

Set the matching SPDX identifier in `pyproject.toml` so packaging metadata does
not contradict the license file:

```toml
license = { text = "BSD-3-Clause" }
classifiers = ["License :: OSI Approved :: BSD License"]
```

Confirm the copyright holder with your employer or institution first. Employment
contracts frequently assign copyright to the institution.

## Attribution

When you build on this package, please cite it. A software citation makes
reuse verifiable and is expected by most journals and funders. Use the version
recorded in `src/myresearchpy/__version__.py`.

## Dependencies

This package depends on NumPy, SciPy and SymPy. Each carries its own license:
NumPy and SciPy use BSD-3-Clause, and SymPy uses BSD-3-Clause. Verify the terms
of any additional dependency you introduce before adding it, since a
permissively licensed project can be affected by the licenses of what it pulls
in.
