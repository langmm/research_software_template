#!/usr/bin/env python
"""Check that this template has been fully adopted by a new project.

A repository created from this template is *not* a research package until the
placeholder identity has been replaced everywhere. Forgetting one occurrence is
easy and the consequences are quiet: a package that installs under the wrong
name, a citation file pointing at someone else's repository, an API reference
pointing at modules that no longer exist.

This script reports the exact locations that still need attention and exits
non-zero while any of them remain, so CI can hold the line until the migration
is finished.

Usage
-----
::

    python scripts/check_template.py            # report and exit non-zero
    python scripts/check_template.py --verbose  # show hints and passing checks
    python scripts/check_template.py --only api-docs,version
    python scripts/check_template.py --root ../other-repo

Run ``--list-checks`` for the available check names. The script has no
third-party dependencies and never modifies files.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Set by --root so the checks can be pointed at a fixture repository. The
# default keeps the checker usable as a plain command in the project it lives in.
_ROOT = REPO_ROOT


def repo_root() -> Path:
    """Return the repository the checks operate on."""
    return _ROOT


def set_repo_root(path: Path) -> None:
    """Point the checks at ``path`` instead of the enclosing repository."""
    global _ROOT
    _ROOT = Path(path).resolve()


# The checker necessarily contains the placeholder strings it searches for, so
# it excludes itself from every content scan.
SELF = Path(__file__).resolve()

# Directories that never contain project source or metadata.
SKIP_DIRS = frozenset(
    {
        ".git",
        ".pixi",
        ".mypy_cache",
        ".pre-commit",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "_build",
        "dist",
        "node_modules",
        "site-packages",
    }
)

# Binary or generated files whose bytes are not meaningful to scan.
SKIP_SUFFIXES = frozenset({".lock", ".mo", ".pdf", ".png", ".ico", ".jpg", ".svg"})


def placeholder_tokens() -> tuple[str, ...]:
    """Return the raw placeholder strings the scan looks for.

    Exposed so that callers, notably the test suite, can refer to the real
    values without writing them as literals of their own.
    """
    return tuple(placeholder.token for placeholder in PLACEHOLDERS)


def _excluded_files() -> frozenset[Path]:
    """Return files that must never be scanned for placeholders.

    The checker itself contains every token it searches for. Its copy inside
    the repository under test is excluded as well, so pointing the checker at a
    fixture that includes the script does not produce self-referential findings.
    """
    return frozenset(
        path.resolve() for path in (SELF, repo_root() / "scripts" / "check_template.py")
    )


# ---------------------------------------------------------------------------
# placeholder definitions
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Placeholder:
    """A literal token that must not survive the migration."""

    token: str
    description: str


PACKAGE_PLACEHOLDER = Placeholder("my" + "researchpy", "the template package name")
AUTHOR_PLACEHOLDER = Placeholder("Your" + " Name", "the author or copyright holder")

PLACEHOLDERS: tuple[Placeholder, ...] = (
    PACKAGE_PLACEHOLDER,
    AUTHOR_PLACEHOLDER,
    Placeholder("you@" + "example.org", "the contact email"),
    Placeholder("your-" + "org", "the GitHub organisation"),
    Placeholder("0000-0000-0000-0000", "the ORCID iD"),
    Placeholder("XXXXXX" + "XX", "the DOI suffix, once minted"),
    # Scoped to the CITATION.cff key so that the very common word "First" is
    # not treated as a placeholder wherever else it appears.
    Placeholder(
        'given-names: "' + "Fir" + 'st"', "the author's given name in CITATION.cff"
    ),
)


# ---------------------------------------------------------------------------
# findings
# ---------------------------------------------------------------------------
@dataclass
class Finding:
    """One problem, anchored to a file and line where possible."""

    check: str
    path: Path
    message: str
    line: int | None = None
    hint: str = ""

    def render(self, *, verbose: bool) -> str:
        """Return the multi-line report entry for this finding."""
        location = str(self.path)
        if self.line is not None:
            location = f"{location}:{self.line}"
        text = f"  {location}\n      {self.message}"
        if self.hint and verbose:
            text = f"{text}\n      hint: {self.hint}"
        return text


@dataclass
class CheckResult:
    """The outcome of a single check."""

    check: str
    findings: list[Finding] = field(default_factory=list)
    error: str = ""

    @property
    def ok(self) -> bool:
        """Return whether this check found nothing to report."""
        return not self.findings and not self.error


# ---------------------------------------------------------------------------
# repository helpers
# ---------------------------------------------------------------------------
def tracked_files() -> Iterator[Path]:
    """Yield repository files worth scanning, skipping caches and binaries."""
    for path in sorted(repo_root().rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if SKIP_DIRS & set(path.relative_to(repo_root()).parts):
            continue
        if path.suffix in SKIP_SUFFIXES:
            continue
        yield path


def read(path: Path) -> str:
    """Return the text of ``path``, or an empty string if it is unreadable."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def find_line(text: str, needle: str, *, limit: int | None = None) -> int | None:
    """Return the 1-based line number of the first unskipped ``needle``."""
    for number, line in enumerate(text.splitlines(), 1):
        if needle not in line:
            continue
        if limit is not None and limit in line:
            continue
        return number
    return None


# ---------------------------------------------------------------------------
# minimal TOML reading
# ---------------------------------------------------------------------------
def _toml_parser():
    """Return the ``loads`` callable of the available TOML parser.

    :mod:`tomllib` is stdlib from 3.11. On 3.10 the backport ``tomli`` is used;
    it is declared as a conditional dependency so both interpreters parse the
    manifest identically. An earlier revision of this script substituted a
    hand-written partial reader here, which silently failed to see keys such as
    ``license`` and reported them as missing.
    """
    try:
        import tomllib
    except ModuleNotFoundError:
        pass
    else:
        return tomllib.loads
    try:
        import tomli
    except ModuleNotFoundError:
        return None
    return tomli.loads


def load_toml(path: Path) -> dict:
    """Parse ``path`` as TOML, or return an empty project table on failure.

    A missing or unparsable manifest is reported by the individual checks rather
    than raised, so one broken file produces a readable finding instead of a
    traceback.
    """
    text = read(path)
    if not text:
        return {}
    loads = _toml_parser()
    if loads is None:
        return {"project": _fallback_project_table(text)}
    try:
        return loads(text)
    except Exception:  # malformed manifest: surface it as an empty document
        return {"project": {}}


def _fallback_project_table(text: str) -> dict:
    """Read the scalar keys of ``[project]`` from a TOML document.

    Recognises ``key = "value"`` and ``key = { text = "value" }`` lines within
    the ``[project]`` table only, which is all this script needs. A manifest
    using forms this reader cannot understand yields fewer keys, and the
    affected check then reports a problem rather than guessing a value.
    """
    start = text.find("[project]")
    if start == -1:
        return {}
    body = text[start + len("[project]") :]
    end = body.find("\n[")
    if end != -1:
        body = body[:end]

    table: dict = {}
    for match in re.finditer(
        r'^\s*(name|version)\s*=\s*(?:"([^"]*)"|\{\s*text\s*=\s*"([^"]*)")',
        body,
        re.MULTILINE,
    ):
        key, plain, nested = match.group(1), match.group(2), match.group(3)
        if key not in table:
            table[key] = plain if plain is not None else nested
    return table


def project_name(manifest: dict) -> str:
    """Return the distribution name from a parsed manifest."""
    return str(manifest.get("project", {}).get("name") or "")


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------
def check_placeholders() -> CheckResult:
    """Report every surviving placeholder token."""
    result = CheckResult(check="placeholders")
    for placeholder in PLACEHOLDERS:
        for path in tracked_files():
            if path.resolve() in _excluded_files():
                continue
            text = read(path)
            if not text or placeholder.token not in text:
                continue
            line = find_line(text, placeholder.token)
            result.findings.append(
                Finding(
                    check=result.check,
                    path=path.relative_to(repo_root()),
                    message=f"contains the placeholder for {placeholder.description}",
                    line=line,
                    hint=f"replace {placeholder.token!r} with the real value",
                )
            )
    return result


def check_version() -> CheckResult:
    """Ensure the declared version agrees everywhere it is recorded.

    The version is a single fact that appears in the packaging manifest, the
    package, and the citation file. Divergence between them produces a build
    that reports one version and installs another.
    """
    result = CheckResult(check="version")

    manifest_path = repo_root() / "pyproject.toml"
    manifest = load_toml(manifest_path)
    project = manifest.get("project", {})
    package_name = project.get("name", "")
    declared = project.get("version")

    version_module = None
    if package_name:
        version_module = repo_root() / "src" / package_name / "__version__.py"
        if not version_module.exists():
            result.error = (
                f"cannot find {version_module.relative_to(repo_root())}; "
                "the project name and src layout disagree"
            )
            return result

    if version_module is None:
        result.error = "could not read the project name from pyproject.toml"
        return result

    module_text = read(version_module)
    match = re.search(r'__version__\s*=\s*"([^"]+)"', module_text)
    if match is None:
        result.error = (
            f"no __version__ string found in {version_module.relative_to(repo_root())}"
        )
        return result
    from_package = match.group(1)

    if declared is None:
        if "version" not in project.get("dynamic", []):
            result.findings.append(
                Finding(
                    check=result.check,
                    path=manifest_path.relative_to(repo_root()),
                    message="declares no version and does not list it as dynamic",
                    hint=f'set version = "{from_package}"',
                )
            )
    elif declared != from_package:
        result.findings.append(
            Finding(
                check=result.check,
                path=manifest_path.relative_to(repo_root()),
                message=(
                    f"declares version {declared!r} but the package reports "
                    f"{from_package!r}"
                ),
                line=find_line(read(manifest_path), f'"{declared}"'),
                hint="keep pyproject.toml and __version__.py in step",
            )
        )

    citation = repo_root() / "CITATION.cff"
    citation_text = read(citation)
    if citation_text:
        for match in re.finditer(r'^\s*version:\s*"([^"]*)"', citation_text, re.M):
            value = match.group(1)
            if value != from_package:
                result.findings.append(
                    Finding(
                        check=result.check,
                        path=citation.relative_to(repo_root()),
                        message=(
                            f"cites version {value!r}, package reports {from_package!r}"
                        ),
                        line=find_line(citation_text, f'"{value}"'),
                        hint="update CITATION.cff to the version being released",
                    )
                )
    return result


def check_package_name() -> CheckResult:
    """Ensure the package name is consistent and the layout follows it."""
    result = CheckResult(check="package-name")
    manifest_path = repo_root() / "pyproject.toml"
    manifest = load_toml(manifest_path)
    name = project_name(manifest)
    if not name:
        result.error = "could not read the project name from pyproject.toml"
        return result

    package_dir = repo_root() / "src" / name
    if not package_dir.is_dir():
        candidates = (
            sorted(p.name for p in (repo_root() / "src").glob("*") if p.is_dir())
            if (repo_root() / "src").is_dir()
            else []
        )
        result.findings.append(
            Finding(
                check=result.check,
                path=manifest_path.relative_to(repo_root()),
                message=f"names the project {name!r} but src/{name}/ does not exist",
                hint=(
                    "rename the package directory to match, or fix the name"
                    + (f" (found: {', '.join(candidates)})" if candidates else "")
                ),
            )
        )
        return result

    # The documentation project name should track the package name.
    conf = repo_root() / "docs" / "conf.py"
    conf_text = read(conf)
    if conf_text:
        match = re.search(r'^project\s*=\s*"([^"]+)"', conf_text, re.M)
        if match and match.group(1) != name:
            result.findings.append(
                Finding(
                    check=result.check,
                    path=conf.relative_to(repo_root()),
                    message=(
                        f"documents {match.group(1)!r} but the package is {name!r}"
                    ),
                    line=find_line(conf_text, f'project = "{match.group(1)}"'),
                    hint='set project = "<package name>"',
                )
            )

    # CITATION.cff should name the same software.
    citation = repo_root() / "CITATION.cff"
    citation_text = read(citation)
    if citation_text:
        match = re.search(r'^title:\s*"([^"]+)"', citation_text, re.M)
        if match and match.group(1) != name:
            result.findings.append(
                Finding(
                    check=result.check,
                    path=citation.relative_to(repo_root()),
                    message=f"cites {match.group(1)!r} but the package is {name!r}",
                    line=find_line(citation_text, f'title: "{match.group(1)}"'),
                    hint=f'set title: "{name}"',
                )
            )
    return result


def check_api_docs() -> CheckResult:
    """Ensure every public module is documented and every page resolves.

    The API reference is generated by autodoc, so a stale module name does not
    raise an error at build time; it silently produces an empty page.
    """
    result = CheckResult(check="api-docs")
    manifest = load_toml(repo_root() / "pyproject.toml")
    name = project_name(manifest)
    package_dir = repo_root() / "src" / name
    if not package_dir.is_dir():
        result.error = "cannot resolve the package directory without a valid name"
        return result

    modules = sorted(
        p.stem
        for p in package_dir.glob("*.py")
        if p.stem not in {"__init__", "__version__"}
    )
    api_dir = repo_root() / "docs" / "api"
    documented: dict[str, Path] = {}
    if api_dir.is_dir():
        for page in sorted(api_dir.glob("*.md")):
            text = read(page)
            match = re.search(r"automodule::\s*([\w.]+)", text)
            if match:
                documented[match.group(1).rsplit(".", 1)[-1]] = page

    for module in modules:
        qualified = f"{name}.{module}"
        if module not in documented:
            result.findings.append(
                Finding(
                    check=result.check,
                    path=(package_dir / f"{module}.py").relative_to(repo_root()),
                    message=f"public module {qualified} has no automodule page",
                    hint=f"create docs/api/{module}.md containing {qualified}",
                )
            )

    for module, page in documented.items():
        if module not in modules:
            result.findings.append(
                Finding(
                    check=result.check,
                    path=page.relative_to(repo_root()),
                    message=(
                        f"documents {name}.{module}, which does not exist in "
                        f"src/{name}/"
                    ),
                    hint="remove the page or restore the module",
                )
            )
    return result


def check_license() -> CheckResult:
    """Ensure the declared license matches the text of the LICENSE file."""
    result = CheckResult(check="license")
    license_path = repo_root() / "LICENSE"
    if not license_path.exists():
        result.findings.append(
            Finding(
                check=result.check,
                path=Path("LICENSE"),
                message="no LICENSE file present",
                hint="add one before publishing; unlicensed code is not open source",
            )
        )
        return result

    manifest_path = repo_root() / "pyproject.toml"
    manifest_text = read(manifest_path)
    manifest = load_toml(manifest_path)
    declared = manifest.get("project", {}).get("license")
    if isinstance(declared, dict):
        declared = declared.get("text")
    if not declared:
        result.findings.append(
            Finding(
                check=result.check,
                path=manifest_path.relative_to(repo_root()),
                message="declares no license",
                hint='add license = { text = "<SPDX id>" }',
            )
        )
        return result

    license_text = read(license_path)
    implied = _license_from_text(license_text)
    if implied is None:
        result.findings.append(
            Finding(
                check=result.check,
                path=license_path.relative_to(repo_root()),
                message="could not identify which license this is",
                hint="verify the file matches the license you intend to apply",
            )
        )
    elif implied != declared:
        result.findings.append(
            Finding(
                check=result.check,
                path=manifest_path.relative_to(repo_root()),
                message=(
                    f"declares license {declared!r} but LICENSE looks like {implied!r}"
                ),
                line=find_line(manifest_text, str(declared)),
                hint="keep the SPDX identifier and the license text in agreement",
            )
        )

    # The copyright line must not be left as the template placeholder. Only the
    # holder-related tokens are relevant here, so they are named rather than
    # selected by position.
    for placeholder in (PACKAGE_PLACEHOLDER, AUTHOR_PLACEHOLDER):
        if placeholder.token in license_text:
            result.findings.append(
                Finding(
                    check=result.check,
                    path=license_path.relative_to(repo_root()),
                    message=(
                        f"copyright line still contains the placeholder for "
                        f"{placeholder.description}"
                    ),
                    line=find_line(license_text, placeholder.token),
                    hint="name the actual copyright holder",
                )
            )
    return result


_LICENSE_SIGNATURES: tuple[tuple[str, str], ...] = (
    ("BSD-3-Clause", "Neither the name of the copyright holder"),
    ("BSD-2-Clause", "Redistributions in binary form must reproduce"),
    ("MIT", "Permission is hereby granted, free of charge"),
    ("Apache-2.0", "Apache License"),
    ("MPL-2.0", "Mozilla Public License"),
    ("GPL-3.0", "GNU GENERAL PUBLIC LICENSE"),
)


def _license_from_text(text: str) -> str | None:
    """Return the SPDX id implied by a license's distinctive wording."""
    if "Neither the name of the copyright holder" in text:
        return "BSD-3-Clause"
    for spdx, marker in _LICENSE_SIGNATURES:
        if marker in text:
            return spdx
    return None


CHECKS = {
    "placeholders": check_placeholders,
    "package-name": check_package_name,
    "version": check_version,
    "api-docs": check_api_docs,
    "license": check_license,
}


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------
def run(names: Iterable[str]) -> list[CheckResult]:
    """Execute the named checks, or all of them when none are given."""
    selected = list(names) if names else list(CHECKS)
    unknown = [name for name in selected if name not in CHECKS]
    if unknown:
        raise SystemExit(
            f"unknown check(s): {', '.join(unknown)}\navailable: {', '.join(CHECKS)}"
        )
    return [CHECKS[name]() for name in selected]


def report(results: list[CheckResult], *, verbose: bool) -> int:
    """Print results and return a process exit status."""
    for result in results:
        if result.error:
            print(f"error [{result.check}]: {result.error}")
            continue
        if result.ok:
            if verbose:
                print(f"ok    [{result.check}]")
            continue
        print(f"fail  [{result.check}] {len(result.findings)} issue(s)")
        for finding in result.findings:
            print(finding.render(verbose=verbose))

    failures = sum(1 for r in results if not r.ok)
    total = len(results)
    if failures:
        print(
            f"\n{failures} of {total} check(s) still need attention. "
            "See docs/contributing.md for the migration checklist."
        )
        return 1
    print(f"\nAll {total} check(s) passed. This project is ready to publish.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run the selected checks and return an exit status."""
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n", 1)[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--only",
        help="comma-separated checks to run (default: all)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print passing checks and remediation hints",
    )
    parser.add_argument(
        "--list-checks",
        action="store_true",
        help="print the available check names and exit",
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="repository to check (default: the enclosing repository)",
    )
    args = parser.parse_args(argv)

    if args.root is not None:
        set_repo_root(args.root)

    if args.list_checks:
        for name, check in CHECKS.items():
            summary = (check.__doc__ or "").strip().splitlines()
            print(f"{name:<14} {summary[0] if summary else ''}")
        return 0

    names = (
        [n.strip() for n in args.only.split(",") if n.strip()] if args.only else None
    )
    return report(run(names), verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
