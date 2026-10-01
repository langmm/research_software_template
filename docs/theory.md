# Analytical Background

This page collects the derivations behind the routines in the package. Keeping
theory next to the implementation is what makes a computational result
*verifiable* rather than merely reproducible.

## Variational principle

For a Hermitian Hamiltonian $\hat{H}$ with ground state energy $E_0$ and any
normalised trial state $\lvert \psi \rangle$,

$$
E_0 \leq \lvert \psi \rangle \langle \psi \rvert \hat{H} \lvert \psi \rangle = E[\psi].
$$

Equality holds only when the trial state is an exact eigenstate. Because the
bound is one-sided, a computed expectation value can never fall below the exact
energy. This is what `variational_energy_hydrogen` exploits: it establishes
$\lvert E_{\text{variational}} - E_0 \rvert$ as an upper bound on the error.

## Basis expansion and the overlap matrix

Expanding a trial state in a non-orthogonal basis gives the secular equation

$$
\lvert \psi \rangle = \sum_n c_n \lvert \phi_n \rangle
\quad \Longrightarrow \quad
\mathbf{H}\, \mathbf{c} = E \mathbf{S}\, \mathbf{c},
$$

with overlap entries $S_{ij} = \langle \phi_i \rvert \phi_j \rangle$. Because
$\mathbf{S}$ is positive definite, the problem admits a complete real spectrum
and can be reduced to standard form by a Cholesky factorisation
$\mathbf{S} = \mathbf{L}\mathbf{L}^{\dagger}$, which is what
`generalized_eigenproblem` delegates to {func}`scipy.linalg.eigh`.

## Gaussian basis and the harmonic oscillator

For the oscillator Hamiltonian

$$
\hat{H} = -\frac{\hbar^2}{2m}\frac{\mathrm{d}^2}{\mathrm{d}x^2} + \frac{1}{2} m \omega^2 x^2,
$$

ladder operators $\hat{a}^\dagger$ and $\hat{a}$ satisfy
$\hat{a} \rvert n \rangle = \sqrt{n} \lvert n - 1 \rangle$, and
$\hat{H} = \hbar \omega \left(\hat{a}^\dagger \hat{a} + \tfrac{1}{2}\right)$. Acting
on $\lvert 0 \rangle$ fixes the zero-point energy, giving

$$
E_n = \hbar \omega \left(n + \tfrac{1}{2}\right), \qquad n \geq 0.
$$

Note the mass dependence: with unit spring constant, $\omega = \sqrt{1/m}$, so
heavier particles have *closer* level spacing. This non-obvious scaling is
exactly the sort of detail a regression test should pin down.

## References

1. D. J. Griffiths, *Introduction to Quantum Mechanics*, 3rd ed., Cambridge
   University Press, 2018.
2. E. J. Heller, *Computational Physics*, Cambridge University Press, 2018.
3. R. P. Feynman, *Statistical Mechanics*, Addison-Wesley, 1972.
