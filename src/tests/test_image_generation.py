import io

import numpy as np

from flame.config import AffineParams, Config, FunctionConfig, SizeConfig
from flame.mp_runner import generate_flame
from flame.render import render_image


def _make_simple_config(iterations: int = 500) -> Config:
    return Config(
        size=SizeConfig(width=64, height=48),
        iteration_count=iterations,
        output_path="test.png",
        threads=1,
        seed=42.0,
        functions=[FunctionConfig(name="linear", weight=1.0)],
        affine_params=AffineParams(),
        gamma_correction=False,
        gamma=2.2,
        symmetry_level=1,
    )


def _image_to_bytes(img) -> bytes:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def test_image_generation_is_reproducible_and_non_empty():
    config = _make_simple_config(iterations=500)

    hist1, colors1 = generate_flame(config)

    height = config.size.height
    width = config.size.width

    assert hist1.shape == (height, width)
    assert colors1.shape == (height, width, 3)

    assert hist1.sum() > 0.0
    assert np.count_nonzero(colors1) > 0

    img1 = render_image(config, hist1, colors1)
    assert img1.size == (width, height)

    hist2, colors2 = generate_flame(config)
    img2 = render_image(config, hist2, colors2)

    data1 = _image_to_bytes(img1)
    data2 = _image_to_bytes(img2)

    assert data1 == data2
