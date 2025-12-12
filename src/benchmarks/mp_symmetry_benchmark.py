"""
Manual benchmark for symmetry overhead in fractal flame generation.

Measures generate_flame() runtime for different symmetry_level values
using a fixed heavy configuration and a fixed number of worker processes.

Not intended to be run as part of automated tests or CI.
"""

import gc
import time

from flame.config import AffineParams, Config, FunctionConfig, SizeConfig
from flame.mp_runner import generate_flame


def _make_benchmark_config(*, threads: int, symmetry_level: int) -> Config:
    return Config(
        size=SizeConfig(width=1600, height=1200),
        iteration_count=1_000_000,
        output_path="benchmark.png",
        threads=threads,
        seed=12.345,
        functions=[FunctionConfig(name="swirl", weight=1.0)],
        affine_params=AffineParams(),
        gamma_correction=False,
        gamma=2.2,
        symmetry_level=symmetry_level,
    )


def _cooldown(seconds: float = 0.3) -> None:
    gc.collect()
    time.sleep(seconds)


def run_symmetry_benchmark() -> None:
    threads = 4
    symmetry_levels = [1, 2, 3, 4, 6, 8]
    results: list[tuple[int, float]] = []

    print("Warming up...")
    warm = _make_benchmark_config(threads=threads, symmetry_level=1)
    generate_flame(warm)
    _cooldown()

    print(
        f"Config: {warm.size.width}x{warm.size.height}, "
        f"iters={warm.iteration_count}, fn=swirl, workers={threads}"
    )

    print("\nRunning benchmark...\n")
    for level in symmetry_levels:
        config = _make_benchmark_config(threads=threads, symmetry_level=level)
        start = time.perf_counter()
        generate_flame(config)
        elapsed = time.perf_counter() - start
        results.append((level, elapsed))
        _cooldown()

    base_time = next(t for level, t in results if level == 1)

    print("Fractal flame symmetry benchmark (heavy load)")
    print("Symmetry | Time (s) | vs sym=1")
    print("--------------------------------")
    for level, elapsed in results:
        ratio = elapsed / base_time if base_time > 0 else 0.0
        print(f"{level:>8} | {elapsed:>8.3f} | {ratio:>8.2f}x")


if __name__ == "__main__":
    run_symmetry_benchmark()
