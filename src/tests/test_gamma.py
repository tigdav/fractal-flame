import numpy as np

from flame.config import AffineParams, Config, FunctionConfig, SizeConfig
from flame.render import render_image


def _make_config(gamma_on: bool) -> Config:
    return Config(
        size=SizeConfig(width=2, height=2),
        iteration_count=10,
        output_path="out.png",
        workers=1,
        seed=1.0,
        functions=[FunctionConfig(name="linear", weight=1.0)],
        affine_params=AffineParams(),
        gamma_correction=gamma_on,
        gamma=2.2,
        symmetry_level=1,
    )


def test_render_image_gamma_correction_changes_pixels():
    hist = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)

    colors = np.ones((2, 2, 3), dtype=np.float64) * 0.8

    cfg_off = _make_config(gamma_on=False)
    arr_off = np.array(render_image(cfg_off, hist, colors), dtype=np.uint8)

    cfg_on = _make_config(gamma_on=True)
    arr_on = np.array(render_image(cfg_on, hist, colors), dtype=np.uint8)

    assert not np.array_equal(arr_off, arr_on)
    assert arr_on.mean() > arr_off.mean()
