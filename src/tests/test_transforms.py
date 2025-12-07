import math

import pytest

from flame.affine import AffineTransform
from flame.config import AffineParams, FunctionConfig
from flame.transforms import (
    VARIATIONS,
    CompiledVariation,
    compile_variations,
    horseshoe,
    linear,
    sinusoidal,
    spherical,
    swirl,
)


def test_linear_identity():
    x, y = 1.5, -2.0
    nx, ny = linear(x, y)
    assert nx == pytest.approx(x)
    assert ny == pytest.approx(y)


def test_swirl_matches_formula():
    x, y = 0.7, -0.3
    r2 = x * x + y * y
    expected_x = x * math.sin(r2) - y * math.cos(r2)
    expected_y = x * math.cos(r2) + y * math.sin(r2)

    nx, ny = swirl(x, y)

    assert nx == pytest.approx(expected_x)
    assert ny == pytest.approx(expected_y)


def test_horseshoe_zero_safe():
    nx, ny = horseshoe(0.0, 0.0)
    assert nx == pytest.approx(0.0)
    assert ny == pytest.approx(0.0)


def test_horseshoe_simple_point():
    nx, ny = horseshoe(1.0, 0.0)
    # r = 1, new_x = (x - y) * (x + y) / r = 1, new_y = 0
    assert nx == pytest.approx(1.0)
    assert ny == pytest.approx(0.0)


def test_spherical_zero_safe():
    nx, ny = spherical(0.0, 0.0)
    assert nx == pytest.approx(0.0)
    assert ny == pytest.approx(0.0)


def test_spherical_inverse_r2():
    x, y = 2.0, 1.0
    r2 = x * x + y * y
    inv_r2 = 1.0 / r2
    expected_x = x * inv_r2
    expected_y = y * inv_r2

    nx, ny = spherical(x, y)

    assert nx == pytest.approx(expected_x)
    assert ny == pytest.approx(expected_y)


def test_sinusoidal_uses_sin():
    x, y = 0.5, -0.75
    nx, ny = sinusoidal(x, y)
    assert nx == pytest.approx(math.sin(x))
    assert ny == pytest.approx(math.sin(y))


def test_variations_registry_contains_all():
    assert VARIATIONS["linear"] is linear
    assert VARIATIONS["swirl"] is swirl
    assert VARIATIONS["horseshoe"] is horseshoe
    assert VARIATIONS["spherical"] is spherical
    assert VARIATIONS["sinusoidal"] is sinusoidal


def test_compile_variations_uses_global_affine_by_default():
    funcs = [FunctionConfig(name="swirl", weight=1.0)]
    global_affine = AffineParams(a=0.5, b=0.1, c=-0.2, d=0.0, e=0.5, f=0.3)

    variations = compile_variations(funcs, global_affine)
    assert len(variations) == 1

    v = variations[0]
    assert isinstance(v, CompiledVariation)
    assert v.name == "swirl"
    assert v.weight == pytest.approx(1.0)
    assert v.func is swirl

    # Check that affine is built from global_affine
    expected_affine = AffineTransform.from_params(global_affine)
    px, py = 0.3, -0.4
    rx_expected = expected_affine.apply(px, py)
    rx_actual = v.affine.apply(px, py)
    assert rx_actual[0] == pytest.approx(rx_expected[0])
    assert rx_actual[1] == pytest.approx(rx_expected[1])


def test_compile_variations_prefers_function_affine_over_global():
    func_affine = AffineParams(a=0.3, b=0.0, c=0.1, d=0.0, e=0.3, f=-0.2)
    funcs = [FunctionConfig(name="horseshoe", weight=0.7, affine_params=func_affine)]
    global_affine = AffineParams(a=0.9, b=0.0, c=0.0, d=0.0, e=0.9, f=0.0)

    variations = compile_variations(funcs, global_affine)
    v = variations[0]

    expected_affine = AffineTransform.from_params(func_affine)
    px, py = -0.2, 0.5
    rx_expected = expected_affine.apply(px, py)
    rx_actual = v.affine.apply(px, py)

    assert rx_actual[0] == pytest.approx(rx_expected[0])
    assert rx_actual[1] == pytest.approx(rx_expected[1])


def test_compile_variations_unknown_name_raises_key_error():
    funcs = [FunctionConfig(name="unknown_variation", weight=1.0)]
    global_affine = AffineParams()

    with pytest.raises(KeyError):
        compile_variations(funcs, global_affine)
