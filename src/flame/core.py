import logging
import random
from typing import List, Tuple

from .affine import AffineTransform
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


def generate_points(config: Config) -> List[Tuple[float, float, str]]:
    """Generate chaotic points for a single-thread fractal flame.

    Args:
        config (Config): Runtime configuration.

    Returns:
        list[tuple[float, float, str]]: Generated points as (x, y, variation_name).
    """
    logger.info("Starting single-thread Chaos Game with %d iterations", config.iteration_count)

    variations = compile_variations(config.functions)
    cumulative = _build_weight_table(variations)
    affine = AffineTransform.from_params(config.affine_params)
    rng = random.Random(config.seed)

    x = 0.0
    y = 0.0

    burn_in = max(100, config.iteration_count // 10)
    total_iterations = burn_in + config.iteration_count

    points: List[Tuple[float, float, str]] = []

    log_step = max(total_iterations // 10, 1)

    for i in range(total_iterations):
        variation = _choose_variation(rng, variations, cumulative)

        x, y = affine.apply(x, y)
        x, y = variation.func(x, y)

        if i >= burn_in:
            points.append((x, y, variation.name))

        if (i + 1) % log_step == 0:
            done = int((i + 1) / total_iterations * 100)
            logger.info("Chaos Game progress: %d%%", done)

    logger.info("Chaos Game finished, generated %d points", len(points))
    return points
