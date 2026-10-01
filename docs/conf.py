"""Sphinx configuration for the myresearchpy documentation.

Build with ``pixi run docs``. The setup wires numpydoc into autodoc so that
the numpydoc-style docstrings in the package become the API reference.
"""

from __future__ import annotations

import os
import sys
from datetime import date
from importlib.metadata import version as _version

sys.path.insert(0, os.path.abspath("../src"))

project = "myresearchpy"
author = "Your Name"
copyright = f"{date.today().year}, {author}"

try:
    release = _version("myresearchpy")
except Exception:
    release = "0.1.0"
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.extlinks",
    "myst_parser",
    "numpydoc",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
master_doc = "index"

autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_rtype = True
napoleon_use_param = True

numpydoc_show_class_members = False
numpydoc_class_members_toctree = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "sympy": ("https://docs.sympy.org/latest", None),
}

extlinks = {
    "issue": ("https://github.com/your-org/myresearchpy/issues/%s", "#%s"),
    "pr": ("https://github.com/your-org/myresearchpy/pull/%s", "#%s"),
}

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
html_title = f"{project} {release}"
html_theme_options = {
    "repository_url": "https://github.com/your-org/myresearchpy",
    "repository_branch": "main",
    "path_to_docs": "docs",
    "use_edit_page_button": True,
    "use_issues_button": True,
    "use_repository_button": True,
}
html_context = {
    "github_user": "your-org",
    "github_repo": "myresearchpy",
    "github_version": "main",
    "doc_path": "docs",
}

htmlhelp_basename = f"{project}-doc"

# numpydoc renders a docstring References section as a footnote-style citation,
# which Sphinx flags as unreferenced because no inline [1] marker points at it.
# The references are rendered correctly, so the warning is noise here.
suppress_warnings = ["ref.citation"]

latex_documents = [
    (master_doc, f"{project}.tex", f"{project} Documentation", author, "manual"),
]
man_pages = [(master_doc, project, f"{project} Documentation", [author], 1)]
texinfo_documents = [
    (
        master_doc,
        project,
        f"{project} Documentation",
        author,
        project,
        "A theoretical research software package.",
        "Miscellaneous",
    ),
]
