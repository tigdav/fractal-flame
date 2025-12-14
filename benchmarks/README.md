# Benchmarks

This directory contains manual performance benchmarks for the fractal flame generator.

These scripts are **not** intended to be executed as part of automated tests or CI.
They are designed to measure performance characteristics under controlled, heavy-load
conditions and to evaluate scalability and performance trade-offs of the implementation.

---

## General notes

- All benchmarks use a fixed, heavy configuration (1600x1200, 1,000,000 iterations).
- Garbage collection and short cooldowns are used between runs to reduce noise.
- Results may vary depending on CPU, OS, and system load.
- Numbers below are provided as reference measurements from a local development machine.

---

## Multi-process scaling benchmark

**Script:** `mp_threads_benchmark.py`

Measures total generation time for different numbers of worker processes.

### Command

```bash
poetry run python benchmarks/mp_threads_benchmark.py
```

### Results

```
Threads | Time (s) | Speedup
------------------------------
      1 |    2.804 |   1.00x
      2 |    1.943 |   1.44x
      4 |    1.406 |   1.99x
      8 |    1.680 |   1.67x
```

### Summary

- Multi-process rendering provides a clear performance improvement over single-process execution.
- Best performance is achieved with 4 worker processes (~2x speedup).
- Using more processes than available CPU resources leads to diminishing returns due to overhead.

---

## Symmetry overhead benchmark

**Script:** `mp_symmetry_benchmark.py`

Measures the performance impact of rotational symmetry during flame generation.

### Command

```bash
poetry run python benchmarks/mp_symmetry_benchmark.py
```

### Results

```
Symmetry | Time (s) | vs sym=1
--------------------------------
       1 |    1.819 |     1.00x
       2 |    1.956 |     1.08x
       3 |    2.501 |     1.37x
       4 |    2.943 |     1.62x
       6 |    3.794 |     2.09x
       8 |    4.665 |     2.56x
```

### Summary

- Rendering time increases with higher symmetry levels, as expected.
- Overhead grows roughly proportionally to the number of duplicated rotations.
- Symmetry provides a controllable quality/performance trade-off.

---

## Gamma correction benchmark

**Script:** `render_gamma_benchmark.py`

Measures rendering time with gamma correction disabled and enabled.
The histogram and color buffers are generated once and reused.

### Command

```bash
poetry run python benchmarks/render_gamma_benchmark.py
```

### Results

```
gamma OFF      | mean=0.070609s | min=0.069633s | median=0.070422s | max=0.072255s
gamma ON (2.2) | mean=0.110619s | min=0.101889s | median=0.107457s | max=0.125808s

Mean overhead: 56.7%
```

### Summary

- Gamma correction introduces a noticeable rendering overhead (~57%).
- The overhead is isolated to the rendering stage and does not affect point generation.
- This behavior is consistent with per-pixel post-processing costs.

---

## Conclusion

The benchmark results confirm that:

- Multi-process rendering significantly improves performance for CPU-bound workloads.
- Symmetry and gamma correction introduce predictable and controllable overhead.
- The implementation demonstrates stable and predictable performance characteristics under different workloads.
