import logging
import time
from multiprocessing import Pool
from typing import List, Tuple

import numpy as np
from numpy.typing import NDArray

from .config import Config
from .core import generate_flame as generate_flame_single

logger = logging.getLogger("fractal_flame.mp")


def _build_worker_config(config: Config, iterations: int, seed_offset: int) -> Config:
    """Build per-worker config with overridden iteration count and seed.

    Args:
        config: Base configuration.
        iterations: Iteration count for this worker.
        seed_offset: Offset to add to base seed.

    Returns:
        New Config instance for a worker.
    """
    return Config(
        size=config.size,
        iteration_count=iterations,
        output_path=config.output_path,
        threads=1,
        seed=config.seed + float(seed_offset),
        functions=config.functions,
        affine_params=config.affine_params,
        gamma_correction=config.gamma_correction,
        gamma=config.gamma,
        symmetry_level=config.symmetry_level,
    )


def _worker_task(config: Config) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Worker entry point for multiprocessing.

    Args:
        config: Per-worker configuration.

    Returns:
        Tuple of (histogram, colors) for this worker.
    """
    return generate_flame_single(config)


def _split_iterations(total: int, workers: int) -> List[int]:
    """Split total iteration count into per-worker chunks.

    Args:
        total: Total iteration count.
        workers: Number of workers.

    Returns:
        List of iteration counts per worker.
    """
    base = total // workers
    extra = total % workers

    chunks: List[int] = []
    for i in range(workers):
        chunk = base + (1 if i < extra else 0)
        chunks.append(chunk)
    return chunks


def generate_flame(config: Config) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Generate fractal flame histogram and colors in single or multi process mode.

    Args:
        config: Runtime configuration.

    Returns:
        Tuple of (histogram, colors) arrays.
    """
    if config.threads <= 1:
        logger.info("Running single-process flame generation")
        return generate_flame_single(config)

    threads = config.threads
    logger.info(
        "Running multi-process flame generation with %d workers and %d iterations",
        threads,
        config.iteration_count,
    )

    start = time.perf_counter()

    iteration_chunks = _split_iterations(config.iteration_count, threads)

    worker_configs: List[Config] = []
    for idx, chunk_iters in enumerate(iteration_chunks):
        worker_config = _build_worker_config(
            config=config,
            iterations=chunk_iters,
            seed_offset=idx,
        )
        worker_configs.append(worker_config)

    with Pool(processes=threads) as pool:
        results = pool.map(_worker_task, worker_configs)

    hist_list: List[NDArray[np.float64]] = []
    color_sum_list: List[NDArray[np.float64]] = []

    for hist, colors in results:
        hist_list.append(hist)
        color_sum_list.append(colors * hist[..., None])

    total_hist = np.sum(hist_list, axis=0)
    total_color_sum = np.sum(color_sum_list, axis=0)

    avg_colors = np.zeros_like(total_color_sum)
    mask = total_hist > 0.0
    if np.any(mask):
        avg_colors[mask] = total_color_sum[mask] / total_hist[mask][..., None]

    elapsed = time.perf_counter() - start
    logger.info(
        "Multi-process flame generation finished in %.3f seconds", elapsed
    )

    return total_hist, avg_colors
