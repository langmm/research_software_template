"""Tests for :mod:`myresearchpy.energy`."""

from __future__ import annotations

import numpy as np
import pytest

from myresearchpy.energy import harmonic_oscillator_energy, variational_energy_hydrogen


def test_ground_state_energy_is_half_hbar_omega() -> None:
    """The n = 0 level must sit at one half of the spacing."""
    assert float(harmonic_oscillator_energy(0)) == pytest.approx(0.5)


def test_level_spacing_is_uniform() -> None:
    """Successive energies of a harmonic oscillator are equally spaced."""
    energies = harmonic_oscillator_energy(np.arange(5))
    assert np.allclose(np.diff(energies), 1.0)


def test_energies_scale_with_hbar_and_inverse_sqrt_mass() -> None:
    """Dimensional analysis fixes the dependence on hbar and m."""
    default = harmonic_oscillator_energy(2)
    assert np.allclose(harmonic_oscillator_energy(2, hbar=2.0), 2.0 * default)
    assert np.allclose(harmonic_oscillator_energy(2, m=4.0), 0.5 * default)


def test_shape_is_preserved_for_array_input() -> None:
    """Vectorised input keeps its shape, per the numpydoc contract."""
    quantum_numbers = np.array([[0, 1], [2, 3]])
    assert harmonic_oscillator_energy(quantum_numbers).shape == (2, 2)


@pytest.mark.parametrize("bad", [-1, 0.5, 2.7])
def test_invalid_quantum_numbers_are_rejected(bad: float) -> None:
    """Negative and non-integer quantum numbers must raise."""
    with pytest.raises(ValueError):
        harmonic_oscillator_energy(bad)


def test_non_positive_mass_is_rejected() -> None:
    """A non-positive mass has no defined frequency."""
    with pytest.raises(ValueError, match="mass"):
        harmonic_oscillator_energy(0, m=0.0)


def test_variational_energy_brackets_the_exact_ground_state() -> None:
    """The discretisation must approach -1/2 from above, never below."""
    exact = -0.5
    energy = variational_energy_hydrogen(grid_points=2000)
    assert exact <= energy < 0.0


def test_variational_energy_converges_to_exact_value() -> None:
    """Refining the grid must approach the analytic ground state energy."""
    exact = -0.5
    coarse = variational_energy_hydrogen(grid_points=200)
    refined = variational_energy_hydrogen(grid_points=1600)

    assert abs(refined - exact) < abs(coarse - exact)
    assert refined == pytest.approx(exact, abs=1e-2)


def test_discretisation_error_is_second_order_in_grid_spacing() -> None:
    """Doubling the resolution must cut the error by roughly four."""
    exact = -0.5
    error_200 = abs(variational_energy_hydrogen(grid_points=200) - exact)
    error_400 = abs(variational_energy_hydrogen(grid_points=400) - exact)
    ratio = error_200 / error_400
    assert 3.0 < ratio < 5.0


def test_truncation_at_smaller_radius_is_unphysical() -> None:
    """A box too small to reach the Bohr radius badly overestimates E0.

    The Bohr radius is the maximum of the hydrogen 1s density, so cutting the
    domain short squeezes the ground state and raises its energy.
    """
    truncated = variational_energy_hydrogen(grid_points=2000, r_max=1.0)
    assert truncated > 0.0


def test_too_few_grid_points_is_rejected() -> None:
    """The radial discretisation needs at least four interior points."""
    with pytest.raises(ValueError, match="at least 4"):
        variational_energy_hydrogen(grid_points=3)


def test_dense_path_rejects_single_grid_point() -> None:
    """A one-point dense Hamiltonian has no spectrum to diagonalise."""
    with pytest.raises(ValueError, match="at least 2"):
        variational_energy_hydrogen(grid_points=1, hamiltonian=np.eye(1))


def test_coulomb_tridiagonal_is_symmetric_and_finite() -> None:
    """The internal discretisation must stay free of numerical artefacts.

    ``1/r`` diverges at the origin, so the singular grid point is excluded.
    """
    from myresearchpy.energy import _coulomb_tridiagonal

    diagonal, off_diagonal = _coulomb_tridiagonal(64, 80.0)

    assert diagonal.shape == (64,)
    assert off_diagonal.shape == (63,)
    assert np.all(np.isfinite(diagonal))
    assert np.all(np.isfinite(off_diagonal))
    assert np.all(off_diagonal < 0.0)
    # Diagonal is the kinetic 1/h**2 minus the Coulomb 1/r at each radius.
    spacing = 80.0 / 65
    radii = spacing * np.arange(1, 65)
    assert np.allclose(diagonal, 1.0 / spacing**2 - 1.0 / radii)
    assert np.allclose(off_diagonal, -0.5 / spacing**2)


def test_coulomb_tridiagonal_enforces_its_own_minimum() -> None:
    """The helper validates its input independently of the public wrapper."""
    from myresearchpy.energy import _coulomb_tridiagonal

    with pytest.raises(ValueError, match="at least 4"):
        _coulomb_tridiagonal(3, 80.0)


def test_non_positive_radius_is_rejected() -> None:
    """A non-positive box radius is meaningless."""
    with pytest.raises(ValueError, match="r_max"):
        variational_energy_hydrogen(r_max=0.0)


def test_variational_energy_rejects_mismatched_hamiltonian() -> None:
    """A Hamiltonian of the wrong shape must be caught early."""
    with pytest.raises(ValueError, match="shape"):
        variational_energy_hydrogen(grid_points=4, hamiltonian=np.eye(3))


def test_diagonal_hamiltonian_reproduces_diagonal_spectrum() -> None:
    """With a diagonal matrix the lowest eigenvalue is the smallest entry."""
    diagonal = np.diag([-3.0, -1.0, 4.0, 0.5])
    assert variational_energy_hydrogen(
        grid_points=4, hamiltonian=diagonal
    ) == pytest.approx(-3.0)


def test_known_two_level_hamiltonian_spectrum() -> None:
    """Validate the eigensolver against an analytically diagonalised case.

    The matrix ``[[0, 1], [1, 0]]`` has the eigenvectors ``(1, -1)/sqrt(2)``
    and ``(1, 1)/sqrt(2)`` with eigenvalues ``-1`` and ``+1``.
    """
    hamiltonian = np.array([[0.0, 1.0], [1.0, 0.0]])
    assert variational_energy_hydrogen(
        grid_points=2, hamiltonian=hamiltonian
    ) == pytest.approx(-1.0)
