import numpy as np
from PIL import Image

from flame.config import AffineParams, Config, SizeConfig
from flame.render import _map_to_pixel, render_image, render_points


def _make_config(
        width: int = 10,
        height: int = 10,
        gamma_correction: bool = False,
        gamma: float = 2.2,
) -> Config:
    return Config(
        size=SizeConfig(width=width, height=height),
        iteration_count=100,
        output_path="dummy.png",
        threads=1,
        seed=1.0,
        functions=[],  # not used by render
        affine_params=AffineParams(),
        gamma_correction=gamma_correction,
        gamma=gamma,
        symmetry_level=1,
    )


def test_map_to_pixel_inside_returns_expected_indices():
    width, height = 100, 50
    col_row = _map_to_pixel(
        x=0.0,
        y=0.0,
        width=width,
        height=height,
        x_min=-1.0,
        x_max=1.0,
        y_min=-1.0,
        y_max=1.0,
    )

    assert col_row is not None
    col, row = col_row
    assert col == 49
    assert row == 24


def test_map_to_pixel_outside_returns_none():
    result = _map_to_pixel(
        x=2.0,
        y=0.0,
        width=100,
        height=50,
        x_min=-1.0,
        x_max=1.0,
        y_min=-1.0,
        y_max=1.0,
    )
    assert result is None


def test_render_points_sets_expected_color_and_size():
    config = _make_config(width=8, height=8)
    points = [(0.0, 0.0, "swirl")]

    image = render_points(config, points, x_min=-1.0, x_max=1.0, y_min=-1.0, y_max=1.0)

    assert isinstance(image, Image.Image)
    assert image.size == (8, 8)

    col, row = _map_to_pixel(0.0, 0.0, 8, 8, -1.0, 1.0, -1.0, 1.0)
    pixel = image.getpixel((col, row))
    assert pixel == (255, 120, 120)


def test_render_image_no_hits_returns_black_image():
    config = _make_config(width=4, height=3, gamma_correction=False)
    histogram = np.zeros((3, 4), dtype=np.float64)
    colors = np.ones((3, 4, 3), dtype=np.float64)

    image = render_image(config, histogram, colors)
    arr = np.array(image)

    assert arr.shape == (3, 4, 3)
    assert np.all(arr == 0)


def test_render_image_with_hits_without_gamma():
    config = _make_config(width=2, height=2, gamma_correction=False)
    histogram = np.zeros((2, 2), dtype=np.float64)
    colors = np.zeros((2, 2, 3), dtype=np.float64)

    histogram[0, 0] = 1.0
    colors[0, 0] = np.array([1.0, 0.5, 0.0])

    image = render_image(config, histogram, colors)
    arr = np.array(image)

    expected = np.array([255, 128, 0], dtype=np.uint8)
    assert np.allclose(arr[0, 0], expected, atol=1)
    assert np.all(arr[1, 1] == 0)


def test_render_image_with_gamma_correction_applies_power():
    config = _make_config(width=2, height=2, gamma_correction=True, gamma=2.0)
    histogram = np.zeros((2, 2), dtype=np.float64)
    colors = np.zeros((2, 2, 3), dtype=np.float64)

    histogram[0, 0] = 1.0
    colors[0, 0] = np.array([0.25, 0.25, 0.25])

    image = render_image(config, histogram, colors)
    arr = np.array(image)

    expected_float = np.sqrt(0.25)  # gamma = 2.0
    expected_value = int(expected_float * 255.0 + 0.5)

    assert np.allclose(arr[0, 0], expected_value, atol=1)
