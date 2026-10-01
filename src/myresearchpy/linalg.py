"""Dense linear algebra helpers used by the variational routines.

Numerical linear algebra is the backbone of most theoretical computational
physics. The routines here deliberately stay on well-conditioned dense paths
so that reference results remain readable and verifiable.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

__all__ = ["generalized_eigenproblem", "expectation_value", "normalize"]


def _as_square(matrix: ArrayLike, name: str) -> NDArray[np.float64]:
    """Validate that ``matrix`` is a square 2-D float array.

    Parameters
    ----------
    matrix : array_like
        Candidate matrix.
    name : str
        Name used in error messages.

    Returns
    -------
    numpy.ndarray
        The validated matrix.

    Raises
    ------
    ValueError
        If the input is not square and two dimensional.
    """
    array = np.asarray(matrix, dtype=np.float64)
    if array.ndim != 2 or array.shape[0] != array.shape[1]:
        raise ValueError(f"{name} must be a square 2-D array, got shape {array.shape}")
    return array


def normalize(vector: ArrayLike) -> NDArray[np.float64]:
    r"""Return ``vector`` scaled to unit Euclidean norm.

    Parameters
    ----------
    vector : array_like
        Non-zero vector to rescale.

    Returns
    -------
    numpy.ndarray
        A copy of ``vector`` with unit norm.

    Raises
    ------
    ValueError
        If ``vector`` is the zero vector.

    Examples
    --------
    >>> normalize([3.0, 4.0]).tolist()
    [0.6, 0.8]
    """
    array = np.asarray(vector, dtype=np.float64)
    norm = float(np.linalg.norm(array))
    if norm == 0.0:
        raise ValueError("cannot normalize the zero vector")
    return array / norm


def expectation_value(operator: ArrayLike, state: ArrayLike) -> float:
    r"""Evaluate the expectation value of an operator in a normalised state.

    For a Hermitian operator :math:`\hat{O}` the expectation value is

    .. math::

        \langle \hat{O} \rangle = \frac{\mathbf{c}^\dagger \hat{O} \mathbf{c}}
        {\mathbf{c}^\dagger \mathbf{c}},

    where the denominator keeps the result independent of the overall scale of
    :math:`\mathbf{c}`.

    Parameters
    ----------
    operator : array_like
        Square operator matrix.
    state : array_like
        State vector of matching dimension.

    Returns
    -------
    float
        The expectation value.

    Raises
    ------
    ValueError
        If the operator is not square or the state dimension does not match.

    Examples
    --------
    >>> float(expectation_value(np.eye(2), [1.0, 1.0]))
    1.0

    References
    ----------
    .. [1] R. P. Feynman, *Statistical Mechanics*, Addison-Wesley, 1972.
    """
    matrix = _as_square(operator, "operator")
    vector = np.asarray(state, dtype=np.float64)

    if vector.ndim != 1 or vector.shape[0] != matrix.shape[0]:
        raise ValueError(
            f"state must be a 1-D vector of length {matrix.shape[0]}, "
            f"got shape {vector.shape}"
        )

    numerator = float(vector.conj() @ (matrix @ vector))
    denominator = float(vector.conj() @ vector)
    if denominator == 0.0:
        raise ValueError("expectation value is undefined for the zero vector")
    return numerator / denominator


def generalized_eigenproblem(
    matrix: ArrayLike,
    off_diagonal: ArrayLike | None = None,
    overlap: ArrayLike | None = None,
    subset_by_index: tuple[int, int] | None = None,
) -> NDArray[np.float64]:
    r"""Solve a symmetric eigenproblem, dense or tridiagonal.

    Three cases are supported, covering the ground state of a discretised
    operator, a standard symmetric matrix, and the generalised problem
    :math:`\mathbf{A} \mathbf{x} = \lambda \mathbf{B} \mathbf{x}` arising from
    expansion in a non-orthogonal basis.

    Parameters
    ----------
    matrix : array_like
        Symmetric square matrix :math:`\mathbf{A}`, or its main diagonal when
        ``off_diagonal`` is given.
    off_diagonal : array_like, optional
        Symmetric sub- and super-diagonal of length ``n - 1``. Requesting this
        switches to :func:`scipy.linalg.eigh_tridiagonal`, which touches
        :math:`\mathcal{O}(n)` memory instead of :math:`\mathcal{O}(n^2)`.
    overlap : array_like, optional
        Symmetric positive-definite matrix :math:`\mathbf{B}`, only valid
        together with a dense ``matrix``. Defaults to the identity, which
        reduces the call to a standard eigenproblem.
    subset_by_index : tuple of int, optional
        Inclusive pair ``(start, stop)`` of 0-based eigenvalue indices to
        return, following the convention of :func:`scipy.linalg.eigh`. Using
        this avoids computing the whole spectrum, which matters when only the
        lowest states are of interest.

    Returns
    -------
    numpy.ndarray
        Eigenvalues in ascending order.

    Raises
    ------
    ValueError
        If ``matrix`` is not square, if the matrix shapes do not match, if
        ``off_diagonal`` has the wrong length, or if ``overlap`` is combined
        with ``off_diagonal``.

    Examples
    --------
    >>> generalized_eigenproblem([[2.0]])
    array([2.])

    Only the lowest eigenvalue is needed for a ground state problem:

    >>> generalized_eigenproblem(np.diag([5.0, 1.0, -2.0]), subset_by_index=(0, 0))
    array([-2.])

    References
    ----------
    .. [1] G. H. Golub and C. F. Van Loan, *Matrix Computations*, 4th ed.,
       Johns Hopkins University Press, 2013. Section 8.4.
    """
    import scipy.linalg

    if off_diagonal is not None:
        if overlap is not None:
            raise ValueError(
                "overlap is not supported with a tridiagonal matrix; "
                "supply a dense matrix instead"
            )
        diagonal = np.asarray(matrix, dtype=np.float64)
        off = np.asarray(off_diagonal, dtype=np.float64)
        if diagonal.ndim != 1:
            raise ValueError(
                "matrix must be a 1-D diagonal when off_diagonal is given, "
                f"got shape {diagonal.shape}"
            )
        if off.ndim != 1 or off.shape[0] != diagonal.shape[0] - 1:
            raise ValueError(
                f"off_diagonal must have length {diagonal.shape[0] - 1}, "
                f"got shape {off.shape}"
            )

        selector = (
            {"select": "i", "select_range": subset_by_index}
            if subset_by_index is not None
            else {}
        )
        eigenvalues = scipy.linalg.eigh_tridiagonal(
            diagonal, off, eigvals_only=True, **selector
        )
        return np.asarray(eigenvalues, dtype=np.float64)

    a = _as_square(matrix, "matrix")

    if overlap is None:
        b = np.eye(a.shape[0])
    else:
        b = _as_square(overlap, "overlap")
        if b.shape != a.shape:
            raise ValueError(
                f"matrix and overlap must share a shape, got {a.shape} and {b.shape}"
            )

    if subset_by_index is None:
        eigenvalues = scipy.linalg.eigh(a, b, eigvals_only=True)
    else:
        eigenvalues = scipy.linalg.eigh(
            a, b, eigvals_only=True, subset_by_index=subset_by_index
        )
    return np.asarray(eigenvalues, dtype=np.float64)
