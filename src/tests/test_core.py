import logging
import math

import numpy as np
import pytest

from flame import core
from flame.affine import AffineTransform
from flame.config import AffineParams, Config, FunctionConfig, SizeConfig
from flame.core import (
    X_MAX,
    X_MIN,
    Y_MAX,
    Y_MIN,
    _apply_symmetry,
    _build_weight_table,
    _choose_variation,
    _map_to_pixel,
    generate_flame,
    generate_points,
)
from flame.transforms import CompiledVariation, linear


def _make_dummy_variation(weight: float = 1.0) -> CompiledVariation:
    affine = AffineTransform.from_params(AffineParams())
    return CompiledVariation(
        name="linear",
        weight=weight,
        func=linear,
        base_color=(1.0, 1.0, 1.0),
        affine=affine,
    )


def _make_simple_config(
    *,
    width: int = 40,
    height: int = 30,
    iters: int = 200,
    symmetry: int = 1,
) -> Config:
    return Config(
        size=SizeConfig(width=width, height=height),
        iteration_count=iters,
        output_path="result.png",
        threads=1,
        seed=5.1234,
        functions=[FunctionConfig(name="swirl", weight=1.0)],
        affine_params=AffineParams(),
        gamma_correction=False,
        gamma=2.2,
        symmetry_level=symmetry,
    )


def test_build_weight_table_normalizes_weights():
    v1 = _make_dummy_variation(weight=1.0)
    v2 = _make_dummy_variation(weight=3.0)

    table = _build_weight_table([v1, v2])

    assert table[-1] == pytest.approx(1.0)
    assert 0.0 < table[0] < table[1] <= 1.0
    # ratio 1:(1+3) => 0.25
    assert table[0] == pytest.approx(0.25, rel=1e-6)


def test_build_weight_table_all_zero_weights_fallback_to_uniform():
    v1 = _make_dummy_variation(weight=0.0)
    v2 = _make_dummy_variation(weight=0.0)
    v3 = _make_dummy_variation(weight=0.0)

    table = _build_weight_table([v1, v2, v3])

    assert table == pytest.approx([1 / 3, 2 / 3, 1.0])


class _FakeRng:
    def __init__(self, value: float):
        self._value = value

    def random(self) -> float:
        return self._value


@pytest.mark.parametrize(
    "value,index",
    [
        (0.0, 0),
        (0.1, 0),
        (0.3, 1),
        (0.8, 2),
    ],
)
def test_choose_variation_respects_cumulative_table(value, index):
    variations = [
        _make_dummy_variation(),
        _make_dummy_variation(),
        _make_dummy_variation(),
    ]
    cumulative = [0.2, 0.5, 1.0]

    rng = _FakeRng(value)
    chosen = _choose_variation(rng, variations, cumulative)

    assert chosen == variations[index]
    assert chosen.affine == variations[index].affine


def test_apply_symmetry_level_one_returns_same_point():
    points = _apply_symmetry(1.0, 2.0, level=1)
    assert points == [(1.0, 2.0)]


def test_apply_symmetry_rotates_around_origin():
    points = _apply_symmetry(1.0, 0.0, level=4)

    # expected 0, 90, 180, 270 degrees
    expected = [
        (1.0, 0.0),
        (0.0, 1.0),
        (-1.0, 0.0),
        (0.0, -1.0),
    ]
    for (px, py), (ex, ey) in zip(points, expected, strict=False):
        assert px == pytest.approx(ex, abs=1e-6)
        assert py == pytest.approx(ey, abs=1e-6)

    r = math.hypot(1.0, 0.0)
    for px, py in points:
        assert math.hypot(px, py) == pytest.approx(r, rel=1e-6)


def test_map_to_pixel_inside_bounds_maps_to_valid_coords():
    width, height = 3, 3
    x = (X_MIN + X_MAX) / 2.0
    y = (Y_MIN + Y_MAX) / 2.0

    col, row = _map_to_pixel(x, y, width, height)

    assert 0 <= col < width
    assert 0 <= row < height


def test_map_to_pixel_outside_bounds_returns_none():
    width, height = 10, 10
    assert _map_to_pixel(X_MAX + 1.0, 0.0, width, height) is None
    assert _map_to_pixel(0.0, Y_MIN - 1.0, width, height) is None


def test_generate_points_produces_expected_number_of_points():
    config = _make_simple_config(iters=50, symmetry=1)

    points = generate_points(config)

    assert len(points) == config.iteration_count
    assert {name for (_, _, name) in points} == {"swirl"}


def test_generate_flame_shapes_and_non_negative_values():
    config = _make_simple_config(width=32, height=24, iters=100, symmetry=1)

    histogram, colors = generate_flame(config)

    assert histogram.shape == (config.size.height, config.size.width)
    assert colors.shape == (config.size.height, config.size.width, 3)

    assert np.all(histogram >= 0.0)
    assert np.all(colors >= 0.0)
    assert np.all(colors <= 1.0 + 1e-6)

    assert np.sum(histogram) > 0.0


def test_generate_flame_symmetry_increases_total_hits():
    base_config = _make_simple_config(width=32, height=24, iters=100, symmetry=1)
    sym_config = _make_simple_config(width=32, height=24, iters=100, symmetry=4)

    hist_base, _ = generate_flame(base_config)
    hist_sym, _ = generate_flame(sym_config)

    hits_base = float(np.sum(hist_base))
    hits_sym = float(np.sum(hist_sym))

    assert hits_base > 0.0
    assert hits_sym >= hits_base


def test_generate_points_logs_progress(caplog):
    config = _make_simple_config(iters=20, symmetry=1)

    with caplog.at_level(logging.INFO, logger="fractal_flame.core"):
        points = generate_points(config)

    assert len(points) == config.iteration_count

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "fractal_flame.core"
    ]
    assert any("Chaos Game progress" in msg for msg in messages)
    assert any("Chaos Game finished, generated" in msg for msg in messages)


def test_generate_flame_logs_progress(caplog):
    config = _make_simple_config(width=16, height=12, iters=20, symmetry=1)

    with caplog.at_level(logging.INFO, logger="fractal_flame.core"):
        histogram, colors = generate_flame(config)

    assert histogram.shape == (config.size.height, config.size.width)
    assert colors.shape == (config.size.height, config.size.width, 3)

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "fractal_flame.core"
    ]
    assert any("Starting histogram-based Chaos Game" in msg for msg in messages)
    assert any("Chaos Game progress" in msg for msg in messages)
    assert any("Chaos Game finished, histogram generated" in msg for msg in messages)


def test_generate_flame_symmetry_level_multiplies_hits():
    width = 64
    height = 64

    base_config = Config(
        size=SizeConfig(width=width, height=height),
        iteration_count=20,
        output_path="result.png",
        threads=1,
        seed=42.0,
        functions=[FunctionConfig(name="linear", weight=1.0)],
        affine_params=AffineParams(),  # identity
        gamma_correction=False,
        gamma=2.2,
        symmetry_level=1,
    )

    hist_single, _ = core.generate_flame(base_config)

    sym_config = Config(
        size=SizeConfig(width=width, height=height),
        iteration_count=20,
        output_path="result.png",
        threads=1,
        seed=42.0,
        functions=[FunctionConfig(name="linear", weight=1.0)],
        affine_params=AffineParams(),
        gamma_correction=False,
        gamma=2.2,
        symmetry_level=5,
    )

    hist_sym, _ = core.generate_flame(sym_config)

    assert hist_single.shape == hist_sym.shape == (height, width)

    single_sum = float(hist_single.sum())
    sym_sum = float(hist_sym.sum())

    assert single_sum > 0.0
    assert sym_sum == pytest.approx(single_sum * 5.0)
