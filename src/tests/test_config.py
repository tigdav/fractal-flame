import json
from types import SimpleNamespace

import pytest

from flame.config import (
    AffineParams,
    Config,
    ConfigError,
    FunctionConfig,
    SizeConfig,
    _parse_affine_params,
    _parse_functions,
    build_config,
    load_json_config,
    validate_config,
)


def _make_empty_args(**overrides):
    """Build argparse-like namespace with all expected fields."""
    base = dict(
        config=None,
        width=None,
        height=None,
        iteration_count=None,
        output_path=None,
        threads=None,
        seed=None,
        affine_params=None,
        functions=None,
        gamma_correction=False,
        gamma=None,
        symmetry_level=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_parse_affine_params_valid():
    params = _parse_affine_params("0.1,0.2,0.3,0.4,0.5,0.6")

    assert isinstance(params, AffineParams)
    assert params.a == pytest.approx(0.1)
    assert params.b == pytest.approx(0.2)
    assert params.c == pytest.approx(0.3)
    assert params.d == pytest.approx(0.4)
    assert params.e == pytest.approx(0.5)
    assert params.f == pytest.approx(0.6)


def test_parse_affine_params_wrong_count_raises():
    with pytest.raises(ConfigError):
        _parse_affine_params("0.1,0.2,0.3")


def test_parse_affine_params_non_float_raises():
    with pytest.raises(ConfigError):
        _parse_affine_params("0.1,0.2,x,0.4,0.5,0.6")


def test_parse_functions_valid_string():
    funcs = _parse_functions("swirl:1.0, horseshoe:0.7")

    assert len(funcs) == 2
    assert funcs[0].name == "swirl"
    assert funcs[0].weight == pytest.approx(1.0)
    assert funcs[0].affine_params is None

    assert funcs[1].name == "horseshoe"
    assert funcs[1].weight == pytest.approx(0.7)


def test_parse_functions_requires_colon():
    with pytest.raises(ConfigError):
        _parse_functions("swirl")


def test_parse_functions_invalid_weight_raises():
    with pytest.raises(ConfigError):
        _parse_functions("swirl:not_a_number")


def test_load_json_config_happy_path(tmp_path):
    config_dict = {"iteration_count": 123}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config_dict), encoding="utf-8")

    loaded = load_json_config(str(path))

    assert loaded == config_dict


def test_load_json_config_missing_file_raises(tmp_path):
    missing = tmp_path / "missing.json"
    with pytest.raises(ConfigError):
        load_json_config(str(missing))


def test_load_json_config_non_object_root_raises(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    with pytest.raises(ConfigError):
        load_json_config(str(path))


def test_load_json_config_invalid_json_raises(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{ invalid json", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_json_config(str(path))


def test_build_config_uses_json_values_when_no_cli_override(tmp_path):
    json_data = {
        "size": {"width": 640, "height": 480},
        "iteration_count": 5000,
        "output_path": "from_json.png",
        "threads": 4,
        "seed": 1.23,
        "functions": [{"name": "swirl", "weight": 1.0}],
        "affine_params": {
            "a": 0.5,
            "b": 0.0,
            "c": 0.1,
            "d": 0.0,
            "e": 0.5,
            "f": -0.2,
        },
        "gamma_correction": True,
        "gamma": 1.8,
        "symmetry_level": 3,
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(json_data), encoding="utf-8")

    args = _make_empty_args(config=str(path))
    config = build_config(args)

    assert config.size.width == 640
    assert config.size.height == 480
    assert config.iteration_count == 5000
    assert config.output_path == "from_json.png"
    assert config.threads == 4
    assert config.seed == pytest.approx(1.23)

    assert len(config.functions) == 1
    assert config.functions[0].name == "swirl"
    assert config.functions[0].weight == pytest.approx(1.0)

    assert config.affine_params.a == pytest.approx(0.5)
    assert config.affine_params.c == pytest.approx(0.1)
    assert config.affine_params.f == pytest.approx(-0.2)

    assert config.gamma_correction is True
    assert config.gamma == pytest.approx(1.8)
    assert config.symmetry_level == 3


def test_build_config_cli_overrides_json(tmp_path):
    json_data = {
        "size": {"width": 640, "height": 480},
        "iteration_count": 5000,
        "output_path": "from_json.png",
        "threads": 2,
        "seed": 1.23,
        "functions": [{"name": "swirl", "weight": 1.0}],
        "affine_params": {"a": 0.5, "b": 0.0, "c": 0.1, "d": 0.0, "e": 0.5, "f": 0.0},
        "gamma_correction": False,
        "gamma": 2.2,
        "symmetry_level": 2,
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(json_data), encoding="utf-8")

    args = _make_empty_args(
        config=str(path),
        width=800,
        height=600,
        iteration_count=9999,
        output_path="from_cli.png",
        threads=8,
        seed=9.99,
        affine_params="0.1,0.2,0.3,0.4,0.5,0.6",
        functions="horseshoe:0.7",
        gamma_correction=True,
        gamma=1.5,
        symmetry_level=5,
    )

    config = build_config(args)

    assert config.size.width == 800
    assert config.size.height == 600
    assert config.iteration_count == 9999
    assert config.output_path == "from_cli.png"
    assert config.threads == 8
    assert config.seed == pytest.approx(9.99)

    assert len(config.functions) == 1
    assert config.functions[0].name == "horseshoe"
    assert config.functions[0].weight == pytest.approx(0.7)

    assert config.affine_params.a == pytest.approx(0.1)
    assert config.affine_params.b == pytest.approx(0.2)
    assert config.affine_params.f == pytest.approx(0.6)

    assert config.gamma_correction is True
    assert config.gamma == pytest.approx(1.5)
    assert config.symmetry_level == 5


def _make_valid_config() -> Config:
    return Config(
        size=SizeConfig(width=800, height=600),
        iteration_count=1000,
        output_path="result.png",
        threads=1,
        seed=5.1234,
        functions=[FunctionConfig(name="swirl", weight=1.0)],
        affine_params=AffineParams(),
        gamma_correction=False,
        gamma=2.2,
        symmetry_level=1,
    )


def test_validate_config_happy_path():
    config = _make_valid_config()
    validate_config(config)


def test_validate_config_invalid_size_raises():
    config = _make_valid_config()
    config.size.width = 0
    with pytest.raises(ConfigError):
        validate_config(config)


def test_validate_config_invalid_iteration_count_raises():
    config = _make_valid_config()
    config.iteration_count = 0
    with pytest.raises(ConfigError):
        validate_config(config)


def test_validate_config_invalid_threads_raises():
    config = _make_valid_config()
    config.threads = 0
    with pytest.raises(ConfigError):
        validate_config(config)


def test_validate_config_requires_functions():
    config = _make_valid_config()
    config.functions = []
    with pytest.raises(ConfigError):
        validate_config(config)


def test_validate_config_requires_non_zero_weight():
    config = _make_valid_config()
    config.functions = [FunctionConfig(name="swirl", weight=0.0)]
    with pytest.raises(ConfigError):
        validate_config(config)


def test_validate_config_gamma_must_be_positive():
    config = _make_valid_config()
    config.gamma = 0.0
    with pytest.raises(ConfigError):
        validate_config(config)


def test_validate_config_symmetry_level_must_be_positive():
    config = _make_valid_config()
    config.symmetry_level = 0
    with pytest.raises(ConfigError):
        validate_config(config)


def test_validate_config_unknown_function_name_raises():
    # ensure error from compile_variations is wrapped into ConfigError
    config = _make_valid_config()
    config.functions = [FunctionConfig(name="unknown_variation", weight=1.0)]

    with pytest.raises(ConfigError):
        validate_config(config)
