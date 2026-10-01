"""Utilities supporting reproducible numerical experiments.

Reproducibility (a CURE principle) depends on more than recording code: the
random state has to be pinned as well. The helpers here make that explicit.
"""

from __future__ import annotations

import platform
import sys
from datetime import datetime, timezone
from typing import Any

import numpy as np

__all__ = ["set_seed", "environment_report"]


def set_seed(seed: int | None = None) -> int:
    """Seed every random number generator used by the package.

    Parameters
    ----------
    seed : int, optional
        Non-negative integer seed. When ``None``, a seed is drawn from system
        entropy, which makes the run deliberately non-reproducible. The chosen
        seed is returned so it can be recorded in logs.

    Returns
    -------
    int
        The seed actually applied.

    Raises
    ------
    ValueError
        If ``seed`` is negative.

    Examples
    --------
    >>> seed = set_seed(1234)
    >>> first = np.random.random()
    >>> set_seed(seed)
    1234
    >>> bool(first == np.random.random())
    True
    """
    if seed is None:
        entropy: int = np.random.SeedSequence().generate_state(1, dtype=np.uint32)[0]
        seed = int(entropy)

    if seed < 0:
        raise ValueError(f"seed must be non-negative, got {seed!r}")

    np.random.seed(seed)
    try:  # pragma: no cover - only present when the package is available
        import random

        random.seed(seed)
    except ImportError:  # pragma: no cover
        pass

    return int(seed)


def environment_report() -> dict[str, Any]:
    """Summarise the runtime environment for provenance records.

    Capturing interpreter, platform and library versions alongside a result is
    what allows a third party to judge whether a numerical difference stems
    from the algorithm or from the environment.

    Returns
    -------
    dict
        Mapping of environment keys to values.

    Examples
    --------
    >>> report = environment_report()
    >>> sorted(report)[:2]
    ['numpy', 'platform']
    """
    import scipy
    import sympy

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "sympy": sympy.__version__,
    }
