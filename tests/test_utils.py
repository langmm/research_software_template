"""Tests for :mod:`myresearchpy.utils`."""

from __future__ import annotations

import numpy as np
import pytest

from myresearchpy.utils import environment_report, set_seed


def test_set_seed_makes_draws_reproducible() -> None:
    """Re-seeding must reproduce the same stream of random numbers."""
    seed = set_seed(1234)
    first = np.random.random(5)
    set_seed(seed)
    assert np.array_equal(first, np.random.random(5))


def test_set_seed_returns_applied_seed() -> None:
    """The returned seed records what was actually used."""
    assert set_seed(7) == 7


def test_set_seed_accepts_none_and_returns_draw() -> None:
    """Passing None draws a seed from entropy and still reports it."""
    seed = set_seed(None)
    assert isinstance(seed, int)
    assert seed >= 0


def test_set_seed_rejects_negative_seed() -> None:
    """A negative seed is outside the accepted domain."""
    with pytest.raises(ValueError, match="non-negative"):
        set_seed(-1)


def test_environment_report_contains_core_versions() -> None:
    """Provenance records need interpreter and library versions."""
    report = environment_report()
    for key in ("timestamp", "python", "platform", "numpy", "scipy", "sympy"):
        assert key in report
    assert isinstance(report["numpy"], str)


def test_public_api_is_exported() -> None:
    """The package surface must expose the documented names."""
    import myresearchpy

    assert set(myresearchpy.__all__) <= set(dir(myresearchpy))
    assert myresearchpy.__version__ == "0.1.0"
