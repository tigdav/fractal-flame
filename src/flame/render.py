import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .config import Config


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
