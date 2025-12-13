import logging
import math
import random
from typing import List, Tuple

import numpy as np
from numpy.typing import NDArray

from .config import Config
from .transforms import CompiledVariation, compile_variations

logger = logging.getLogger("fractal_flame.core")

X_MIN = -1.5
X_MAX = 1.5
Y_MIN = -1.0
Y_MAX = 1.0


def _build_weight_table(variations: List[CompiledVariation]) -> List[float]:
    weights = [max(v.weight, 0.0) for v in variations]
    total = sum(weights)
    if total <= 0.0:
        total = float(len(weights))
        weights = [1.0 for _ in weights]

    cumulative: List[float] = []
    acc = 0.0
    for w in weights:
        acc += w / total
        cumulative.append(acc)
    cumulative[-1] = 1.0
    return cumulative


def _choose_variation(
    rng: random.Random,
    variations: List[CompiledVariation],
    cumulative: List[float],
) -> CompiledVariation:
    r = rng.random()
    for v, threshold in zip(variations, cumulative):
        if r <= threshold:
            return v
    return variations[-1]


def _apply_symmetry(x: float, y: float, level: int) -> List[Tuple[float, float]]:
    if level <= 1:
        return [(x, y)]

    points: List[Tuple[float, float]] = []
    for k in range(level):
        angle = 2.0 * math.pi * k / float(level)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        px = x * cos_a - y * sin_a
        py = x * sin_a + y * cos_a
        points.append((px, py))
    return points


def _map_to_pixel(
    x: float,
    y: float,
    width: int,
    height: int,
) -> Tuple[int, int] | None:
    if x < X_MIN or x > X_MAX or y < Y_MIN or y > Y_MAX:
        return None

    nx = (x - X_MIN) / (X_MAX - X_MIN)
    ny = (y - Y_MIN) / (Y_MAX - Y_MIN)

    col = int(nx * (width - 1))
    row = int((1.0 - ny) * (height - 1))

    if 0 <= col < width and 0 <= row < height:
        return col, row
    return None


def generate_points(config: Config) -> List[Tuple[float, float, str]]:
    """Generate chaotic points for a single-thread fractal flame.

    Args:
        config: Runtime configuration.

    Returns:
        Generated points as (x, y, variation_name).
    """
    logger.info(
        "Starting single-thread Chaos Game with %d iterations", config.iteration_count
    )

    variations = compile_variations(config.functions, config.affine_params)
    cumulative = _build_weight_table(variations)
    rng = random.Random(config.seed)

    x = rng.uniform(-1.0, 1.0)
    y = rng.uniform(-1.0, 1.0)

    burn_in = max(100, config.iteration_count // 10)
    total_iterations = burn_in + config.iteration_count

    points: List[Tuple[float, float, str]] = []

    log_step = max(total_iterations // 10, 1)

    for i in range(total_iterations):
        variation = _choose_variation(rng, variations, cumulative)

        x, y = variation.affine.apply(x, y)
        x, y = variation.func(x, y)

        if i >= burn_in:
            points.append((x, y, variation.name))

        if (i + 1) % log_step == 0:
            done = int((i + 1) / total_iterations * 100)
            logger.info("Chaos Game progress: %d%%", done)

    logger.info("Chaos Game finished, generated %d points", len(points))
    return points


def generate_flame(config: Config) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Generate histogram and color buffer for a fractal flame.

    Args:
        config: Runtime configuration.

    Returns:
        tuple[NDArray[np.float64], NDArray[np.float64]]:
            Histogram array with hit counts and color accumulator array.
    """
    width = config.size.width
    height = config.size.height

    histogram = np.zeros((height, width), dtype=np.float64)
    color_acc = np.zeros((height, width, 3), dtype=np.float64)
    hits = np.zeros((height, width), dtype=np.float64)

    variations = compile_variations(config.functions, config.affine_params)
    cumulative = _build_weight_table(variations)
    rng = random.Random(config.seed)

    x = rng.uniform(-1.0, 1.0)
    y = rng.uniform(-1.0, 1.0)
    r = 0.0
    g = 0.0
    b = 0.0

    burn_in = max(100, config.iteration_count // 10)
    total_iterations = burn_in + config.iteration_count

    log_step = max(total_iterations // 10, 1)
    mix = 0.5

    logger.info(
        "Starting histogram-based Chaos Game with %d iterations", config.iteration_count
    )

    for i in range(total_iterations):
        variation = _choose_variation(rng, variations, cumulative)

        x, y = variation.affine.apply(x, y)
        x, y = variation.func(x, y)

        base_r, base_g, base_b = variation.base_color
        r = (1.0 - mix) * r + mix * base_r
        g = (1.0 - mix) * g + mix * base_g
        b = (1.0 - mix) * b + mix * base_b

        points = _apply_symmetry(x, y, config.symmetry_level)

        if i >= burn_in:
            for px, py in points:
                mapped = _map_to_pixel(px, py, width, height)
                if mapped is None:
                    continue

                col, row = mapped
                histogram[row, col] += 1.0
                color_acc[row, col, 0] += r
                color_acc[row, col, 1] += g
                color_acc[row, col, 2] += b
                hits[row, col] += 1.0

        if (i + 1) % log_step == 0:
            done = int((i + 1) / total_iterations * 100)
            logger.info("Chaos Game progress: %d%%", done)

    mask = hits > 0.0
    if np.any(mask):
        color_acc[mask] /= hits[mask][..., None]

    logger.info("Chaos Game finished, histogram generated")
    return histogram, color_acc
