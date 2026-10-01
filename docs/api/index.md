# API Reference

The API reference is generated directly from the numpydoc docstrings in the
package, so it cannot drift out of date with the source.

```{toctree}
:maxdepth: 2

energy
linalg
utils
```

## Module overview

| Module | Purpose |
| --- | --- |
| `myresearchpy.energy` | Analytical spectra and variational energy estimates |
| `myresearchpy.linalg` | Dense generalised eigenproblems and expectation values |
| `myresearchpy.utils` | Seeding and provenance reporting |

## Analytic baselines

| Quantity | Exact value | Routine |
| --- | --- | --- |
| Oscillator ground state | $E_0 = \hbar\omega/2$ | `harmonic_oscillator_energy(0)` |
| Oscillator spacing | $\hbar\omega$ | `np.diff(harmonic_oscillator_energy(...))` |
| Hydrogen ground state | $E_0 = -1/2$ Ha | `variational_energy_hydrogen(...)` |
