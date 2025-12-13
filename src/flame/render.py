from collections.abc import Iterable

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .config import Config

FUNCTION_COLORS = {
    "linear": (255, 255, 255),
    "swirl": (255, 120, 120),
    "horseshoe": (120, 255, 120),
    "spherical": (120, 120, 255),
    "sinusoidal": (255, 255, 120),
}


def _map_to_pixel(
    x: float,
    y: float,
    width: int,
    height: int,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> tuple[int, int] | None:
    """Map fractal coordinates to pixel coordinates.

    Args:
        x (float): X coordinate in fractal space.
        y (float): Y coordinate in fractal space.
        width (int): Image width in pixels.
        height (int): Image height in pixels.
        x_min (float): Minimum X in fractal space.
        x_max (float): Maximum X in fractal space.
        y_min (float): Minimum Y in fractal space.
        y_max (float): Maximum Y in fractal space.

    Returns:
        tuple[int, int] | None: Pixel coordinates (col, row) or None if out of bounds.

    """
    if x < x_min or x > x_max or y < y_min or y > y_max:
        return None

    nx = (x - x_min) / (x_max - x_min)
    ny = (y - y_min) / (y_max - y_min)

    col = int(nx * (width - 1))
    row = int((1.0 - ny) * (height - 1))

    if 0 <= col < width and 0 <= row < height:
        return col, row
    return None


def render_points(
    config: Config,
    points: Iterable[tuple[float, float, str]],
    x_min: float = -1.5,
    x_max: float = 1.5,
    y_min: float = -1.0,
    y_max: float = 1.0,
) -> Image.Image:
    """Render chaotic points into an RGB image.

    Args:
        config (Config): Runtime configuration.
        points (Iterable[tuple[float, float, str]]): Points as (x, y, variation_name).
        x_min (float): Minimum X in fractal space.
        x_max (float): Maximum X in fractal space.
        y_min (float): Minimum Y in fractal space.
        y_max (float): Maximum Y in fractal space.

    Returns:
        PIL.Image.Image: Rendered image.

    """
    width = config.size.width
    height = config.size.height

    image = Image.new("RGB", (width, height), (0, 0, 0))
    pixels = image.load()

    for x, y, func_name in points:
        mapped = _map_to_pixel(x, y, width, height, x_min, x_max, y_min, y_max)
        if mapped is None:
            continue

        col, row = mapped
        color = FUNCTION_COLORS.get(func_name, (200, 200, 200))
        pixels[col, row] = color

    return image


def render_image(
    config: Config,
    histogram: NDArray[np.float64],
    colors: NDArray[np.float64],
) -> Image.Image:
    """Render histogram and color buffer into an RGB image.

    Args:
        config (Config): Runtime configuration.
        histogram (NDArray[np.float64]): Hit counts per pixel.
        colors (NDArray[np.float64]): Averaged RGB colors per pixel in [0, 1].

    Returns:
        PIL.Image.Image: Rendered image.

    """
    hist = histogram.copy()
    hist[hist < 0.0] = 0.0

    nonzero = hist > 0.0
    if np.any(nonzero):
        hist[nonzero] = np.log1p(hist[nonzero])
        max_val = float(hist.max())
        if max_val > 0.0:
            hist /= max_val

    img_float = colors * hist[..., None]
    img_float = np.clip(img_float, 0.0, 1.0)

    if config.gamma_correction:
        gamma = config.gamma if config.gamma > 0.0 else 2.2
        img_float = np.power(img_float, 1.0 / gamma)

    img_float = np.clip(img_float, 0.0, 1.0)
    img_uint8 = (img_float * 255.0 + 0.5).astype("uint8")

    return Image.fromarray(img_uint8, mode="RGB")
