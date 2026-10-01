"""Tests for ``scripts/check_template.py``.

The checker is the thing that stops a half-finished migration from being
published, so its detection logic is tested directly. Rather than copying and
breaking the real repository, each test builds a small synthetic repository that
exercises one failure mode, which keeps the tests fast and independent of the
project's own identity.

Placeholder strings are read from the checker through
``placeholder_tokens()`` rather than written here as literals. That matters: a
test file containing the literal template package name would be flagged by the
placeholder scan in CI, and would break the moment the project was renamed.

Fixtures are built under ``.check_template_fixtures/`` inside the repository and
removed afterwards.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_template.py"
SCRATCH_ROOT = REPO_ROOT / ".check_template_fixtures"


def load_checker():
    """Import the checker as a module so its constants can be read.

    The module is registered in ``sys.modules`` before execution because
    ``@dataclass`` looks its defining module up while the class body runs.
    """
    spec = importlib.util.spec_from_file_location("check_template", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_template"] = module
    spec.loader.exec_module(module)
    return module


CHECKER = load_checker()
# Resolved from the checker so that no placeholder appears as a literal in this
# file. Indexing by position is deliberate: a literal here would be flagged by
# the placeholder scan, and would break on rename.
(
    PKG_PLACEHOLDER,
    AUTHOR_PLACEHOLDER,
    EMAIL_PLACEHOLDER,
    ORG_PLACEHOLDER,
    ORCID_PLACEHOLDER,
    DOI_PLACEHOLDER,
    GIVEN_NAMES_PLACEHOLDER,
) = CHECKER.placeholder_tokens()

LICENSE_BSD3 = """BSD 3-Clause License

Copyright (c) 2026, A Real Person
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


def manifest(
    name: str, *, version: str = "1.2.3", license_id: str = "BSD-3-Clause"
) -> str:
    """Return a pyproject.toml body for a synthetic project."""
    return (
        "[build-system]\n"
        'requires = ["hatchling"]\n'
        'build-backend = "hatchling.build"\n\n'
        "[project]\n"
        f'name = "{name}"\n'
        f'version = "{version}"\n'
        'requires-python = ">=3.10"\n'
        f'license = {{ text = "{license_id}" }}\n\n'
        "[tool.hatch.version]\n"
        f'path = "src/{name}/__version__.py"\n'
    )


@pytest.fixture
def make_repo() -> Iterator[Callable[[str], Path]]:
    """Return a factory that builds a synthetic project on disk.

    The default repository is fully migrated: correct package name, matching
    version, documented modules and a consistent license. Tests then break one
    thing and assert the relevant check notices.
    """
    made: list[Path] = []

    def build(name: str = "analytic", **overrides: str) -> Path:
        root = SCRATCH_ROOT / name
        shutil.rmtree(root, ignore_errors=True)
        package = str(overrides.get("package", "analytic"))

        (root / "src" / package).mkdir(parents=True)
        (root / "docs" / "api").mkdir(parents=True)

        (root / "pyproject.toml").write_text(
            manifest(package, **overrides), encoding="utf-8"
        )
        (root / "src" / package / "__version__.py").write_text(
            f'__version__ = "{overrides.get("version", "1.2.3")}"\n', encoding="utf-8"
        )
        (root / "src" / package / "energy.py").write_text(
            '"""Energy routines."""\n', encoding="utf-8"
        )
        (root / "docs" / "api" / "energy.md").write_text(
            f"# energy\n\n```{{eval-rst}}\n.. automodule:: {package}.energy\n"
            "   :members:\n```\n",
            encoding="utf-8",
        )
        (root / "docs" / "conf.py").write_text(
            f'project = "{package}"\n', encoding="utf-8"
        )
        (root / "LICENSE").write_text(LICENSE_BSD3, encoding="utf-8")
        (root / "CITATION.cff").write_text(
            f'title: "{package}"\nversion: "{overrides.get("version", "1.2.3")}"\n',
            encoding="utf-8",
        )
        made.append(root)
        return root

    try:
        yield build
    finally:
        for path in made:
            shutil.rmtree(path, ignore_errors=True)
        if SCRATCH_ROOT.exists() and not any(SCRATCH_ROOT.iterdir()):
            SCRATCH_ROOT.rmdir()


def run_checker(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the checker against ``root`` and capture its output."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


# ---------------------------------------------------------------------------
# behaviour on a correctly migrated repository
# ---------------------------------------------------------------------------
def test_fully_migrated_repository_passes_every_check(
    make_repo: Callable[..., Path],
) -> None:
    """A complete, consistent project must produce a clean report."""
    result = run_checker(make_repo("clean"))
    assert result.returncode == 0, result.stdout
    assert "All 5 check(s) passed" in result.stdout


def test_placeholders_are_found_wherever_they_appear(
    make_repo: Callable[..., Path],
) -> None:
    """Any surviving placeholder must be reported with its file and line."""
    root = make_repo("placeholder")
    (root / "src" / "analytic" / "leaked.py").write_text(
        f'"""Module."""\n\n# TODO: rename {PKG_PLACEHOLDER}\n', encoding="utf-8"
    )

    result = run_checker(root, "--only", "placeholders")
    assert result.returncode == 1
    assert "leaked.py:3" in result.stdout


def test_every_placeholder_category_is_detected(
    make_repo: Callable[..., Path],
) -> None:
    """Each placeholder in the table must be caught, not just the first."""
    root = make_repo("all-placeholders")
    (root / "notes.md").write_text(
        "\n".join(
            [
                f"package {PKG_PLACEHOLDER}",
                f"author {AUTHOR_PLACEHOLDER}",
                f"email {EMAIL_PLACEHOLDER}",
                f"org {ORG_PLACEHOLDER}",
                f"orcid {ORCID_PLACEHOLDER}",
                f"doi {DOI_PLACEHOLDER}",
                f"citation {GIVEN_NAMES_PLACEHOLDER}",
            ]
        ),
        encoding="utf-8",
    )

    result = run_checker(root, "--only", "placeholders")
    assert result.returncode == 1
    assert "notes.md" in result.stdout
    # Seven distinct placeholders in one file.
    assert result.stdout.count("contains the placeholder") == 7


def test_given_names_placeholder_is_scoped_to_the_citation_key(
    make_repo: Callable[..., Path],
) -> None:
    """A surviving given-names key in CITATION.cff must be caught.

    The first name is common English, so the placeholder is qualified with its
    citation key. Matching the bare word would turn ordinary prose in the
    documentation into a permanent finding.
    """
    root = make_repo("given-names")
    citation = root / "CITATION.cff"
    injected = f'title: "analytic"\n{GIVEN_NAMES_PLACEHOLDER}'
    citation.write_text(
        citation.read_text().replace('title: "analytic"', injected),
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "The first step is to read this.\n", encoding="utf-8"
    )

    result = run_checker(root, "--only", "placeholders")
    assert result.returncode == 1
    assert "CITATION.cff" in result.stdout
    assert "README.md" not in result.stdout


# ---------------------------------------------------------------------------
# version consistency
# ---------------------------------------------------------------------------
def test_version_drift_between_manifest_and_package_is_detected(
    make_repo: Callable[..., Path],
) -> None:
    """A manifest version that disagrees with __version__.py must fail."""
    root = make_repo("version-drift")
    (root / "pyproject.toml").write_text(
        manifest("analytic", version="9.9.9"), encoding="utf-8"
    )

    result = run_checker(root, "--only", "version")
    assert result.returncode == 1
    assert "9.9.9" in result.stdout
    assert "1.2.3" in result.stdout


def test_version_drift_in_citation_file_is_detected(
    make_repo: Callable[..., Path],
) -> None:
    """A CITATION.cff version that disagrees with the package must fail."""
    root = make_repo("citation-drift")
    citation = root / "CITATION.cff"
    citation.write_text(
        citation.read_text().replace('version: "1.2.3"', 'version: "0.0.1"'),
        encoding="utf-8",
    )

    result = run_checker(root, "--only", "version")
    assert result.returncode == 1
    assert "0.0.1" in result.stdout


def test_missing_version_module_is_reported_as_an_error(
    make_repo: Callable[..., Path],
) -> None:
    """A missing __version__.py must be explained, not silently ignored."""
    root = make_repo("no-version-module")
    (root / "src" / "analytic" / "__version__.py").unlink()

    result = run_checker(root, "--only", "version")
    assert result.returncode == 1
    assert "error [version]" in result.stdout


# ---------------------------------------------------------------------------
# package name and layout
# ---------------------------------------------------------------------------
def test_project_name_without_matching_directory_is_detected(
    make_repo: Callable[..., Path],
) -> None:
    """A renamed manifest with an unrenamed directory must fail."""
    root = make_repo("layout-mismatch")
    (root / "pyproject.toml").write_text(manifest("elsewhere"), encoding="utf-8")

    # The hint naming the directory it did find is verbose-only output.
    result = run_checker(root, "--only", "package-name", "--verbose")
    assert result.returncode == 1
    assert "elsewhere" in result.stdout
    assert "analytic" in result.stdout  # names the directory it did find


def test_docs_naming_a_different_project_is_detected(
    make_repo: Callable[..., Path],
) -> None:
    """docs/conf.py must agree with the package name."""
    root = make_repo("docs-mismatch")
    (root / "docs" / "conf.py").write_text(
        'project = "somethingelse"\n', encoding="utf-8"
    )

    result = run_checker(root, "--only", "package-name")
    assert result.returncode == 1
    assert "somethingelse" in result.stdout


def test_citation_naming_a_different_project_is_detected(
    make_repo: Callable[..., Path],
) -> None:
    """CITATION.cff must agree with the package name."""
    root = make_repo("citation-name-mismatch")
    citation = root / "CITATION.cff"
    citation.write_text(
        citation.read_text().replace('title: "analytic"', 'title: "wrong"'),
        encoding="utf-8",
    )

    result = run_checker(root, "--only", "package-name")
    assert result.returncode == 1
    assert "wrong" in result.stdout


# ---------------------------------------------------------------------------
# API documentation
# ---------------------------------------------------------------------------
def test_undocumented_module_is_detected(make_repo: Callable[..., Path]) -> None:
    """A public module with no automodule page must fail."""
    root = make_repo("undocumented")
    (root / "src" / "analytic" / "linalg.py").write_text(
        '"""Linear algebra."""\n', encoding="utf-8"
    )

    result = run_checker(root, "--only", "api-docs")
    assert result.returncode == 1
    assert "linalg" in result.stdout


def test_api_page_for_a_missing_module_is_detected(
    make_repo: Callable[..., Path],
) -> None:
    """An API page pointing at a nonexistent module must fail."""
    root = make_repo("stale-api")
    (root / "docs" / "api" / "ghost.md").write_text(
        "# ghost\n\n```{eval-rst}\n.. automodule:: analytic.ghost\n   :members:\n```\n",
        encoding="utf-8",
    )

    result = run_checker(root, "--only", "api-docs")
    assert result.returncode == 1
    assert "ghost" in result.stdout


def test_private_modules_are_not_required_to_be_documented(
    make_repo: Callable[..., Path],
) -> None:
    """Dunder modules must not demand a page of their own."""
    root = make_repo("private-modules")
    (root / "src" / "analytic" / "__init__.py").write_text(
        '"""Package."""\n', encoding="utf-8"
    )

    result = run_checker(root, "--only", "api-docs")
    assert result.returncode == 0, result.stdout


# ---------------------------------------------------------------------------
# license
# ---------------------------------------------------------------------------
def test_license_spdx_mismatch_is_detected(make_repo: Callable[..., Path]) -> None:
    """A manifest license that contradicts the LICENSE text must fail."""
    root = make_repo("license-mismatch", license_id="MIT")

    result = run_checker(root, "--only", "license")
    assert result.returncode == 1
    assert "MIT" in result.stdout
    assert "BSD-3-Clause" in result.stdout


def test_placeholder_copyright_in_license_is_detected(
    make_repo: Callable[..., Path],
) -> None:
    """A LICENSE that still names the template author must fail."""
    root = make_repo("license-author")
    (root / "LICENSE").write_text(
        LICENSE_BSD3.replace("A Real Person", AUTHOR_PLACEHOLDER), encoding="utf-8"
    )

    result = run_checker(root, "--only", "license")
    assert result.returncode == 1
    assert "copyright" in result.stdout.lower()


def test_missing_license_file_is_detected(make_repo: Callable[..., Path]) -> None:
    """An unlicensed repository must fail, since it is not open source."""
    root = make_repo("no-license")
    (root / "LICENSE").unlink()

    result = run_checker(root, "--only", "license")
    assert result.returncode == 1
    assert "LICENSE" in result.stdout


def test_unrecognisable_license_text_is_reported(
    make_repo: Callable[..., Path],
) -> None:
    """A LICENSE whose terms cannot be identified must not pass silently."""
    root = make_repo("odd-license")
    (root / "LICENSE").write_text(
        "Some bespoke terms nobody has seen.\n", encoding="utf-8"
    )

    result = run_checker(root, "--only", "license")
    assert result.returncode == 1
    assert "identify" in result.stdout


# ---------------------------------------------------------------------------
# command line interface
# ---------------------------------------------------------------------------
def test_list_checks_names_every_check() -> None:
    """--list-checks must enumerate the available checks and succeed."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--list-checks"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    for name in ("placeholders", "package-name", "version", "api-docs", "license"):
        assert name in result.stdout


def test_unknown_check_name_is_rejected(make_repo: Callable[..., Path]) -> None:
    """A misspelled check name must not be silently ignored."""
    result = run_checker(make_repo("unknown-check"), "--only", "not-a-check")
    assert result.returncode != 0
    assert "unknown check" in result.stderr


def test_only_selection_limits_the_checks_run(
    make_repo: Callable[..., Path],
) -> None:
    """--only must run exactly the requested checks."""
    root = make_repo("only-selection")
    (root / "docs" / "conf.py").write_text('project = "wrong"\n', encoding="utf-8")

    result = run_checker(root, "--only", "api-docs", "--verbose")
    assert result.returncode == 0, result.stdout
    assert "api-docs" in result.stdout


def test_verbose_mode_adds_hints_and_passes(make_repo: Callable[..., Path]) -> None:
    """--verbose reports passing checks and prints remediation hints."""
    root = make_repo("verbose")
    (root / "src" / "analytic" / "leak.py").write_text(
        f"# {PKG_PLACEHOLDER}\n", encoding="utf-8"
    )

    quiet = run_checker(root, "--only", "placeholders")
    loud = run_checker(root, "--only", "placeholders", "--verbose")
    assert "hint:" not in quiet.stdout
    assert "hint:" in loud.stdout


def test_checker_excludes_its_own_copy_from_the_scan(
    make_repo: Callable[..., Path],
) -> None:
    """A copy of the checker inside the scanned tree must not be flagged."""
    root = make_repo("self-scan")
    (root / "scripts").mkdir()
    shutil.copy(SCRIPT, root / "scripts" / "check_template.py")

    result = run_checker(root, "--only", "placeholders")
    assert result.returncode == 0, result.stdout


def test_root_defaults_to_the_enclosing_repository() -> None:
    """Run without --root, the checker inspects the repository it lives in.

    The shipped template is deliberately unmigrated, so this must fail. That
    also guards against the checker passing vacuously on the placeholder
    repository it is distributed from.
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "still need attention" in result.stdout
