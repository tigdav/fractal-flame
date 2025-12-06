import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

from .config import FunctionConfig

VariationFunc = Callable[[float, float], tuple[float, float]]


def linear(x: float, y: float) -> tuple[float, float]:
    return x, y


def swirl(x: float, y: float) -> tuple[float, float]:
    r2 = x * x + y * y
    sin_r2 = math.sin(r2)
    cos_r2 = math.cos(r2)
    new_x = x * sin_r2 - y * cos_r2
    new_y = x * cos_r2 + y * sin_r2
    return new_x, new_y


def horseshoe(x: float, y: float) -> tuple[float, float]:
    r = math.hypot(x, y)
    if r == 0.0:
        return 0.0, 0.0
    new_x = (x - y) * (x + y) / r
    new_y = 2.0 * x * y / r
    return new_x, new_y


def spherical(x: float, y: float) -> tuple[float, float]:
    r2 = x * x + y * y
    if r2 == 0.0:
        return 0.0, 0.0
    inv_r2 = 1.0 / r2
    new_x = x * inv_r2
    new_y = y * inv_r2
    return new_x, new_y


def sinusoidal(x: float, y: float) -> tuple[float, float]:
    return math.sin(x), math.sin(y)


VARIATIONS: Dict[str, VariationFunc] = {
    "linear": linear,
    "swirl": swirl,
    "horseshoe": horseshoe,
    "spherical": spherical,
    "sinusoidal": sinusoidal,
}

VARIATION_BASE_COLORS: Dict[str, Tuple[float, float, float]] = {
    "linear": (1.0, 1.0, 1.0),
    "swirl": (1.0, 0.3, 0.3),
    "horseshoe": (0.3, 1.0, 0.3),
    "spherical": (0.3, 0.3, 1.0),
    "sinusoidal": (1.0, 1.0, 0.3),
}


@dataclass
class CompiledVariation:
    name: str
    weight: float
    func: VariationFunc
    base_color: Tuple[float, float, float]


def compile_variations(functions: List[FunctionConfig]) -> List[CompiledVariation]:
    """Compile list of variations from FunctionConfig entries.

    Args:
        functions (list[FunctionConfig]): Functions from Config.

    Returns:
        list[CompiledVariation]: Compiled variation list.

    Raises:
        KeyError: If unknown variation name is encountered.
    """
    compiled: List[CompiledVariation] = []

    for fn in functions:
        func = VARIATIONS.get(fn.name)
        if func is None:
            raise KeyError(f"Unknown variation name: {fn.name}")

        base_color = VARIATION_BASE_COLORS.get(fn.name, (0.8, 0.8, 0.8))
        compiled.append(
            CompiledVariation(
                name=fn.name,
                weight=fn.weight,
                func=func,
                base_color=base_color,
            )
        )

    return compiled
