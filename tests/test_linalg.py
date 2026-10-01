"""Tests for :mod:`myresearchpy.linalg`."""

from __future__ import annotations

import numpy as np
import pytest

from myresearchpy.linalg import expectation_value, generalized_eigenproblem, normalize


def test_normalize_returns_unit_vector() -> None:
    """A normalised vector must have Euclidean norm one."""
    assert float(np.linalg.norm(normalize([3.0, 4.0]))) == pytest.approx(1.0)


def test_normalize_rejects_zero_vector() -> None:
    """The zero vector has no direction."""
    with pytest.raises(ValueError, match="zero"):
        normalize([0.0, 0.0])


def test_expectation_value_of_identity_is_one() -> None:
    """The identity operator returns the norm of the state, which is one."""
    assert expectation_value(np.eye(3), [1.0, 1.0, 1.0]) == pytest.approx(1.0)


def test_expectation_value_is_scale_invariant() -> None:
    """Rescaling the state must not change the expectation value."""
    state = [1.0, 2.0, -0.5]
    operator = np.array([[2.0, 0.5, 0.0], [0.5, 1.0, 0.25], [0.0, 0.25, 3.0]])
    assert expectation_value(operator, state) == pytest.approx(
        expectation_value(operator, 17.0 * np.asarray(state))
    )


def test_expectation_value_of_diagonal_operator() -> None:
    """For a diagonal operator the answer is a weighted sum of squares."""
    operator = np.diag([1.0, 2.0])
    assert expectation_value(operator, [1.0, 1.0]) == pytest.approx(1.5)


def test_expectation_value_rejects_mismatched_state() -> None:
    """The state dimension must match the operator dimension."""
    with pytest.raises(ValueError, match="state"):
        expectation_value(np.eye(2), [1.0, 1.0, 1.0])


def test_expectation_value_rejects_zero_state() -> None:
    """The expectation value is undefined for the zero vector."""
    with pytest.raises(ValueError, match="zero"):
        expectation_value(np.eye(2), [0.0, 0.0])


def test_generalized_eigenproblem_defaults_to_identity_overlap() -> None:
    """Omitting the overlap matrix must fall back to the identity."""
    matrix = np.array([[2.0, 0.0], [0.0, 3.0]])
    assert np.allclose(generalized_eigenproblem(matrix), [2.0, 3.0])


def test_generalized_eigenproblem_solves_sturm_liouville_form() -> None:
    """A non-trivial overlap matrix shifts the spectrum.

    For ``A = [[2, 1], [1, 2]]`` and ``B = [[2, 0], [0, 1]]`` the secular
    equation ``det(A - l B) = 0`` gives ``2*l**2 - 6*l + 3 = 0``, whose roots
    are ``(3 +/- sqrt(3)) / 2``.
    """
    matrix = np.array([[2.0, 1.0], [1.0, 2.0]])
    overlap = np.array([[2.0, 0.0], [0.0, 1.0]])
    eigenvalues = generalized_eigenproblem(matrix, overlap=overlap)
    expected = np.array([3.0 - np.sqrt(3.0), 3.0 + np.sqrt(3.0)]) / 2.0
    assert np.allclose(eigenvalues, expected)


def test_generalized_eigenproblem_subset_selects_lowest_state() -> None:
    """An inclusive index range of ``(0, 0)`` isolates the ground state."""
    matrix = np.diag([5.0, 1.0, -2.0, 8.0])
    assert np.allclose(generalized_eigenproblem(matrix, subset_by_index=(0, 0)), [-2.0])


def test_generalized_eigenproblem_subset_range_is_inclusive() -> None:
    """``(0, 2)`` must return three eigenvalues, following the scipy convention."""
    matrix = np.diag([5.0, 1.0, -2.0, 8.0])
    assert np.allclose(
        generalized_eigenproblem(matrix, subset_by_index=(0, 2)), [-2.0, 1.0, 5.0]
    )


def test_tridiagonal_problem_matches_dense_equivalent() -> None:
    """Passing only the diagonals must give the dense result."""
    rng = np.random.default_rng(7)
    off = rng.standard_normal(5)
    diagonal = rng.standard_normal(6)

    dense = np.diag(diagonal) + np.diag(off, 1) + np.diag(off, -1)
    assert np.allclose(
        generalized_eigenproblem(diagonal, off), generalized_eigenproblem(dense)
    )


def test_tridiagonal_subset_selects_ground_state() -> None:
    """Ground state selection must work on the tridiagonal path too."""
    diagonal = np.array([1.0, 2.0, 3.0, 4.0])
    off = np.array([0.1, 0.1, 0.1])
    lowest = generalized_eigenproblem(diagonal, off, subset_by_index=(0, 0))
    assert len(lowest) == 1
    assert lowest[0] < diagonal.min()


def test_tridiagonal_rejects_wrong_off_diagonal_length() -> None:
    """The off-diagonal must have exactly ``n - 1`` entries."""
    with pytest.raises(ValueError, match="off_diagonal"):
        generalized_eigenproblem(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0]))


def test_tridiagonal_rejects_dense_matrix() -> None:
    """A dense matrix must be rejected when an off-diagonal is supplied."""
    with pytest.raises(ValueError, match="1-D"):
        generalized_eigenproblem(np.eye(3), np.array([1.0, 2.0]))


def test_overlap_with_tridiagonal_is_rejected() -> None:
    """The two matrix paths are mutually exclusive."""
    with pytest.raises(ValueError, match="overlap"):
        generalized_eigenproblem(
            np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0]), overlap=np.eye(3)
        )


def test_generalized_eigenproblem_returns_ascending_eigenvalues() -> None:
    """Eigenvalues must come back sorted, since lowest states matter most."""
    rng = np.random.default_rng(0)
    matrix = rng.standard_normal((6, 6))
    matrix = 0.5 * (matrix + matrix.T)
    eigenvalues = generalized_eigenproblem(matrix)
    assert np.all(np.diff(eigenvalues) >= 0)


def test_generalized_eigenproblem_rejects_shape_mismatch() -> None:
    """Matrix and overlap must have the same shape."""
    with pytest.raises(ValueError, match="shape"):
        generalized_eigenproblem(np.eye(2), overlap=np.eye(3))


def test_generalized_eigenproblem_rejects_non_square_input() -> None:
    """Non-square matrices are rejected with a clear message."""
    with pytest.raises(ValueError, match="square"):
        generalized_eigenproblem(np.ones((2, 3)))
