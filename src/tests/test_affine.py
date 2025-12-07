import math

from flame.affine import AffineTransform
from flame.config import AffineParams


def test_from_params_copies_all_fields():
    params = AffineParams(a=0.5, b=0.1, c=-0.2, d=0.3, e=0.8, f=1.5)

    transform = AffineTransform.from_params(params)

    assert transform.a == params.a
    assert transform.b == params.b
    assert transform.c == params.c
    assert transform.d == params.d
    assert transform.e == params.e
    assert transform.f == params.f


def test_apply_identity_transform_returns_same_point():
    transform = AffineTransform(a=1.0, b=0.0, c=0.0, d=0.0, e=1.0, f=0.0)

    x, y = 0.3, -0.7
    new_x, new_y = transform.apply(x, y)

    assert new_x == x
    assert new_y == y


def test_apply_pure_translation():
    transform = AffineTransform(a=1.0, b=0.0, c=2.0, d=0.0, e=1.0, f=-1.0)

    x, y = -0.5, 0.5
    new_x, new_y = transform.apply(x, y)

    assert new_x == x + 2.0
    assert new_y == y - 1.0


def test_apply_scale_and_rotation_like():
    # 90-degree rotation matrix:
    # x' = 0 * x - 1 * y
    # y' = 1 * x + 0 * y
    transform = AffineTransform(a=0.0, b=-1.0, c=0.0, d=1.0, e=0.0, f=0.0)

    x, y = 1.0, 0.0
    new_x, new_y = transform.apply(x, y)

    assert math.isclose(new_x, 0.0, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(new_y, 1.0, rel_tol=1e-9, abs_tol=1e-9)
