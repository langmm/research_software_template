"""Analytical energy spectra and numerical bound-state estimates.

The module pairs exact results with a numerical solver. That pairing is
deliberate: an exact formula can validate the solver, and the solver can extend
the formula beyond where it is tractable. Every routine is a side-effect free
function with a documented contract, so a result can be reproduced exactly by
anyone re-running the same call.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

__all__ = ["harmonic_oscillator_energy", "variational_energy_hydrogen"]


def harmonic_oscillator_energy(
    n: ArrayLike,
    hbar: float = 1.0,
    m: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return the energy spectrum of the 1D quantum harmonic oscillator.

    The stationary states are labelled by the quantum number :math:`n \geq 0`
    and carry the energies

    .. math::

        E_n = \hbar \omega \left(n + \tfrac{1}{2}\right),
        \qquad \omega = \sqrt{k / m},

    written here for a unit spring constant :math:`k = 1`. The mass dependence
    is worth noting: with :math:`k` fixed, heavier particles have *closer* level
    spacing, since :math:`\omega \propto 1/\sqrt{m}`.

    Parameters
    ----------
    n : array_like
        Quantum numbers. Must be non-negative and integer valued.
    hbar : float, default 1.0
        Reduced Planck constant in the units of the model.
    m : float, default 1.0
        Particle mass. Must be strictly positive.

    Returns
    -------
    numpy.ndarray
        Energies, in the same shape as ``n``.

    Raises
    ------
    ValueError
        If ``m`` is not positive, or if ``n`` contains negative or non-integer
        entries.

    Examples
    --------
    >>> float(harmonic_oscillator_energy(0))
    0.5
    >>> harmonic_oscillator_energy([0, 1]).tolist()
    [0.5, 1.5]

    References
    ----------
    .. [1] D. J. Griffiths, *Introduction to Quantum Mechanics*, 3rd ed.,
       Cambridge University Press, 2018. Chapter 2.3.
    """
    quantum_numbers = np.asarray(n, dtype=np.float64)

    if m <= 0:
        raise ValueError(f"mass must be strictly positive, got {m!r}")
    if np.any(quantum_numbers < 0):
        raise ValueError("quantum numbers must be non-negative")
    if not np.all(np.equal(np.mod(quantum_numbers, 1), 0)):
        raise ValueError("quantum numbers must be integer valued")

    omega = np.sqrt(1.0 / m)
    return hbar * omega * (quantum_numbers + 0.5)


def variational_energy_hydrogen(
    grid_points: int = 2000,
    r_max: float = 80.0,
    hamiltonian: ArrayLike | None = None,
) -> float:
    r"""Estimate the hydrogen ground state energy by finite differences.

    The radial Schrödinger equation in atomic units,

    .. math::

        -\tfrac{1}{2} \psi''(r) - \frac{1}{r} \psi(r) = E \psi(r),

    is discretised on a uniform grid with second-order central differences and
    Dirichlet boundary conditions. The exact ground state energy is
    :math:`-\tfrac{1}{2}`, which makes this routine a convenient benchmark: the
    estimate approaches it from above as the grid is refined.

    Parameters
    ----------
    grid_points : int, default 2000
        Number of interior radial grid points. Must be at least 4 when the
        Coulomb Hamiltonian is built internally, or at least 2 when an
        explicit ``hamiltonian`` is supplied.
    r_max : float, default 80.0
        Outer radius in Bohr radii. Must exceed ``r_min``.
    hamiltonian : array_like, optional
        Optional dense symmetric Hamiltonian of shape
        ``(grid_points, grid_points)``. Supplying this bypasses the radial
        discretisation, which is useful for testing the eigensolver against
        problems with known spectra. When omitted, the Coulomb Hamiltonian is
        built internally.

    Returns
    -------
    float
        The ground state energy estimate, an upper bound on the exact value.

    Raises
    ------
    ValueError
        If ``grid_points`` is too small for the requested path, if ``r_max`` is
        not positive, or if ``hamiltonian`` has the wrong shape.

    Notes
    -----
    The discretisation error is second order in the grid spacing, so the
    deviation from :math:`-\tfrac{1}{2}` falls off as ``grid_points ** -2``.
    Truncating at a finite ``r_max`` also biases the estimate upward, since
    confining the wavefunction cannot lower its energy.

    Examples
    --------
    >>> energy = variational_energy_hydrogen(grid_points=2000)
    >>> bool(-0.5 <= energy < 0.0)
    True

    References
    ----------
    .. [1] R. Courant and D. Hilbert, *Methods of Mathematical Physics*,
       Vol. I, Wiley, 1953.
    .. [2] N. J. Higham, *Accuracy and Stability of Numerical Algorithms*,
       2nd ed., SIAM, 2002. Chapter 3.
    """
    if r_max <= 0:
        raise ValueError(f"r_max must be positive, got {r_max!r}")

    from myresearchpy.linalg import generalized_eigenproblem

    if hamiltonian is None:
        if grid_points < 4:
            raise ValueError(
                f"grid_points must be at least 4 for the radial "
                f"discretisation, got {grid_points!r}"
            )
        diagonal, off_diagonal = _coulomb_tridiagonal(grid_points, r_max)
        eigenvalues = generalized_eigenproblem(
            diagonal, off_diagonal, subset_by_index=(0, 0)
        )
        return float(eigenvalues[0])

    if grid_points < 2:
        raise ValueError(
            f"grid_points must be at least 2 for a dense hamiltonian, "
            f"got {grid_points!r}"
        )

    matrix = np.asarray(hamiltonian, dtype=np.float64)
    if matrix.shape != (grid_points, grid_points):
        raise ValueError(
            f"hamiltonian must have shape {(grid_points, grid_points)}, "
            f"got {matrix.shape}"
        )

    eigenvalues = generalized_eigenproblem(matrix, subset_by_index=(0, 0))
    return float(eigenvalues[0])


def _coulomb_tridiagonal(
    grid_points: int,
    r_max: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    r"""Build the tridiagonal Coulomb Hamiltonian in atomic units.

    The kinetic operator :math:`-\tfrac{1}{2}\mathrm{d}^2/\mathrm{d}r^2`
    becomes ``1/h**2`` on the diagonal and ``-1/(2*h**2)`` off diagonal, while
    the Coulomb term contributes ``-1/r_i``. The singular grid point at the
    origin is excluded, since ``1/r`` diverges there and Dirichlet conditions
    are imposed at both ends of the box.

    Parameters
    ----------
    grid_points : int
        Number of interior radial grid points.
    r_max : float
        Outer radius of the box in Bohr radii.

    Returns
    -------
    diagonal : numpy.ndarray
        Main diagonal of length ``grid_points``.
    off_diagonal : numpy.ndarray
        Sub- and super-diagonal of length ``grid_points - 1``.

    Raises
    ------
    ValueError
        If fewer than 4 grid points are requested, since the tridiagonal
        solver needs at least that many to isolate a single eigenvalue.
    """
    if grid_points < 4:
        raise ValueError(f"grid_points must be at least 4, got {grid_points!r}")

    spacing = r_max / (grid_points + 1)
    radii = spacing * np.arange(1, grid_points + 1, dtype=np.float64)

    diagonal = 1.0 / spacing**2 - 1.0 / radii
    off_diagonal = np.full(grid_points - 1, -0.5 / spacing**2)
    return diagonal, off_diagonal
