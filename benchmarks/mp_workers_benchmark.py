"""Manual performance benchmark for fractal flame generation.

This script measures execution time of generate_flame()
for 1, 2, 4 and 8 worker processes using a fixed heavy configuration.

Not intended to be run as part of automated tests or CI.
"""

import gc
import time

from flame.config import AffineParams, Config, FunctionConfig, SizeConfig
from flame.mp_runner import generate_flame


def _make_benchmark_config(workers: int) -> Config:
    return Config(
        size=SizeConfig(width=1600, height=1200),
        iteration_count=1_000_000,
        output_path="benchmark.png",
        workers=workers,
        seed=12.345,
        functions=[FunctionConfig(name="swirl", weight=1.0)],
        affine_params=AffineParams(),
        gamma_correction=False,
        gamma=2.2,
        symmetry_level=1,
    )


def _cooldown(seconds: float = 0.3) -> None:
    gc.collect()
    time.sleep(seconds)


def run_workers_benchmark() -> None:
    """Run worker-count benchmark for generate_flame().

    Warms up once, then measures runtime for several worker counts under a heavy
    fixed config and prints a simple speedup table.
    """
    worker_counts = [1, 2, 4, 8]
    results: list[tuple[int, float]] = []

    print("Warming up...")
    warm = _make_benchmark_config(workers=1)
    generate_flame(warm)
    _cooldown()

    print(
        f"Config: {warm.size.width}x{warm.size.height}, "
        f"iters={warm.iteration_count}, fn=swirl"
    )

    print("\nRunning benchmark...\n")
    for workers in worker_counts:
        config = _make_benchmark_config(workers=workers)
        start = time.perf_counter()
        generate_flame(config)
        elapsed = time.perf_counter() - start
        results.append((workers, elapsed))
        _cooldown()

    print("Fractal flame benchmark (heavy load)")
    print("Workers | Time (s) | Speedup")
    print("------------------------------")

    base_time = results[0][1]
    for workers, elapsed in results:
        speedup = base_time / elapsed if elapsed > 0 else 0
        print(f"{workers:>7} | {elapsed:>8.3f} | {speedup:>6.2f}x")


if __name__ == "__main__":
    run_workers_benchmark()
