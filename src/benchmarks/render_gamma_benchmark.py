"""
Manual benchmark for gamma correction overhead during rendering.

Measures render_image() runtime with gamma correction off vs on,
using a fixed histogram/colors generated once.

Not intended to be run as part of automated tests or CI.
"""

import gc
import statistics
import time

from flame.config import AffineParams, Config, FunctionConfig, SizeConfig
from flame.mp_runner import generate_flame
from flame.render import render_image


def _make_base_config(*, threads: int, gamma_correction: bool) -> Config:
    return Config(
        size=SizeConfig(width=1600, height=1200),
        iteration_count=1_000_000,
        output_path="benchmark.png",
        threads=threads,
        seed=12.345,
        functions=[FunctionConfig(name="swirl", weight=1.0)],
        affine_params=AffineParams(),
        gamma_correction=gamma_correction,
        gamma=2.2,
        symmetry_level=1,
    )


def _cooldown(seconds: float = 0.2) -> None:
    gc.collect()
    time.sleep(seconds)


def _measure_render(config: Config, hist, colors, repeats: int) -> list[float]:
    render_image(config, hist, colors)
    _cooldown(0.05)

    timings: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        render_image(config, hist, colors)
        timings.append(time.perf_counter() - start)
    return timings


def _print_stats(label: str, timings: list[float]) -> None:
    print(
        f"{label:<14} | "
        f"mean={statistics.mean(timings):.6f}s | "
        f"min={min(timings):.6f}s | "
        f"median={statistics.median(timings):.6f}s | "
        f"max={max(timings):.6f}s"
    )


def run_render_gamma_benchmark() -> None:
    workers = 4
    repeats = 7

    print("Generating fixed histogram/colors (one-time)...")
    gen_cfg = _make_base_config(threads=workers, gamma_correction=False)
    hist, colors = generate_flame(gen_cfg)
    _cooldown()

    print(
        f"Config: {gen_cfg.size.width}x{gen_cfg.size.height}, "
        f"iters={gen_cfg.iteration_count}, fn=swirl, workers={workers}, repeats={repeats}"
    )

    cfg_off = _make_base_config(threads=workers, gamma_correction=False)
    cfg_on = _make_base_config(threads=workers, gamma_correction=True)

    print("\nMeasuring render time...\n")
    off_times = _measure_render(cfg_off, hist, colors, repeats=repeats)
    on_times = _measure_render(cfg_on, hist, colors, repeats=repeats)

    print("Render gamma benchmark")
    print("Mode")
    print("---------------------------------------------------------------")
    _print_stats("gamma OFF", off_times)
    _print_stats("gamma ON (2.2)", on_times)

    off_mean = statistics.mean(off_times)
    on_mean = statistics.mean(on_times)
    overhead = (on_mean / off_mean - 1.0) * 100.0 if off_mean > 0 else 0.0

    print(f"\nMean overhead: {overhead:.1f}%")
    print("Note: histogram/colors are generated once and reused for both modes.")


if __name__ == "__main__":
    run_render_gamma_benchmark()
