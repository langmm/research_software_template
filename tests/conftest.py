"""Pytest configuration shared by every test module."""

from __future__ import annotations

import numpy as np
import pytest

from myresearchpy.utils import set_seed


@pytest.fixture(autouse=True)
def _seeded_session() -> None:
    """Seed the global RNG before each test for deterministic comparisons."""
    set_seed(20240101)


@pytest.fixture
def rng() -> np.random.Generator:
    """Return a private, explicitly seeded generator.

    Returns
    -------
    numpy.random.Generator
        Generator isolated from the global NumPy state.
    """
    return np.random.default_rng(1234)
