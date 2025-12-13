import numpy as np

from flame import core
from flame.config import AffineParams, Config, FunctionConfig, SizeConfig
from flame.render import render_image


def _make_linear_config(
    *,
    width: int = 16,
    height: int = 16,
    iters: int = 50,
    seed: float = 123.0,
) -> Config:
    return Config(
        size=SizeConfig(width=width, height=height),
        iteration_count=iters,
        output_path="result.png",
        threads=1,
        seed=seed,
        functions=[FunctionConfig(name="linear", weight=1.0)],
        affine_params=AffineParams(),
        gamma_correction=False,
        gamma=2.2,
        symmetry_level=1,
    )


def test_small_pipeline_is_deterministic_and_non_empty():
    config = _make_linear_config()

    hist1, colors1 = core.generate_flame(config)
    img1 = render_image(config, hist1, colors1)
    arr1 = np.asarray(img1)

    assert arr1.shape == (config.size.height, config.size.width, 3)
    assert arr1.dtype == np.uint8
    assert arr1.max() > 0

    hist2, colors2 = core.generate_flame(config)
    img2 = render_image(config, hist2, colors2)
    arr2 = np.asarray(img2)

    assert np.array_equal(arr1, arr2)

    config_other_seed = _make_linear_config(seed=999.0)
    hist3, colors3 = core.generate_flame(config_other_seed)
    img3 = render_image(config_other_seed, hist3, colors3)
    arr3 = np.asarray(img3)

    assert not np.array_equal(arr1, arr3)
