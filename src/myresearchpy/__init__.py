"""A theoretical research software package built on FAIR and CURE principles."""

from myresearchpy.__version__ import __version__
from myresearchpy.energy import (
    harmonic_oscillator_energy,
    variational_energy_hydrogen,
)
from myresearchpy.linalg import generalized_eigenproblem
from myresearchpy.utils import set_seed

__all__ = [
    "__version__",
    "harmonic_oscillator_energy",
    "variational_energy_hydrogen",
    "generalized_eigenproblem",
    "set_seed",
]
