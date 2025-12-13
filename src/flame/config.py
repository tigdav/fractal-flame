import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


class ConfigError(Exception):
    """Raised when configuration is invalid."""


AFFINE_PARAM_COUNT = 6

DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_ITERATION_COUNT = 2500
DEFAULT_OUTPUT_PATH = "result.png"
DEFAULT_THREADS = 1
DEFAULT_SEED = 5.1234
DEFAULT_GAMMA = 2.2
DEFAULT_SYMMETRY_LEVEL = 1
DEFAULT_FUNCTION = "swirl"


JsonMapping = Mapping[str, object]


def _raise_config(msg: str) -> None:
    raise ConfigError(msg)


@dataclass
class SizeConfig:
    """Image size configuration."""

    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT


@dataclass
class AffineParams:
    """Affine transformation parameters (a, b, c, d, e, f)."""

    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 0.0
    e: float = 1.0
    f: float = 0.0


@dataclass
class FunctionConfig:
    """Single variation configuration.

    Attributes:
        name: Variation name (e.g., "swirl").
        weight: Selection weight used when choosing a variation.
        affine_params: Optional per-function affine parameters.

    """

    name: str
    weight: float
    affine_params: AffineParams | None = None


@dataclass
class Config:
    """Full runtime configuration for the fractal flame generator."""

    size: SizeConfig
    iteration_count: int
    output_path: str
    threads: int
    seed: float
    functions: list[FunctionConfig]
    affine_params: AffineParams
    gamma_correction: bool = False
    gamma: float = DEFAULT_GAMMA
    symmetry_level: int = DEFAULT_SYMMETRY_LEVEL


def load_json_config(path: str) -> JsonMapping:
    """Load JSON configuration file into plain dictionary."""
    try:
        config_path = Path(path)
        if not config_path.exists():
            msg = f"Config file not found: {path}"
            _raise_config(msg)

        with config_path.open("r", encoding="utf-8") as f:
            data: object = json.load(f)

        if not isinstance(data, dict):
            msg = "JSON config root must be an object"
            _raise_config(msg)
    except json.JSONDecodeError as exc:
        msg = f"Failed to parse JSON config: {exc}"
        raise ConfigError(msg) from exc
    except OSError as exc:
        msg = f"Failed to read config file: {exc}"
        raise ConfigError(msg) from exc
    else:
        return data


def _parse_affine_params(value: str) -> AffineParams:
    parts = value.split(",")
    if len(parts) != AFFINE_PARAM_COUNT:
        msg = "Affine params must have 6 comma-separated values a,b,c,d,e,f"
        _raise_config(msg)

    try:
        a, b, c, d, e, f = (float(p.strip()) for p in parts)
    except ValueError as exc:
        msg = f"Affine params must be floats: {value}"
        raise ConfigError(msg) from exc

    return AffineParams(a=a, b=b, c=c, d=d, e=e, f=f)


def _parse_functions(value: str) -> list[FunctionConfig]:
    functions: list[FunctionConfig] = []

    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item:
            continue

        if ":" not in item:
            msg = f"Function spec must be name:weight, got: {item}"
            _raise_config(msg)

        name, weight_str = item.split(":", 1)
        name = name.strip()

        try:
            weight = float(weight_str.strip())
        except ValueError as exc:
            msg = f"Invalid weight for function '{name}': {weight_str}"
            raise ConfigError(msg) from exc

        functions.append(FunctionConfig(name=name, weight=weight))

    if not functions:
        msg = "At least one function must be specified"
        _raise_config(msg)

    return functions


def _as_dict(value: object) -> JsonMapping | None:
    return value if isinstance(value, dict) else None


def _as_list(value: object) -> list[object] | None:
    return value if isinstance(value, list) else None


def _apply_size(config: Config, data: JsonMapping) -> None:
    size = _as_dict(data.get("size"))
    if size is None:
        return

    width = size.get("width")
    height = size.get("height")

    if width is not None:
        config.size.width = int(width)
    if height is not None:
        config.size.height = int(height)


def _apply_scalar_fields(config: Config, data: JsonMapping) -> None:
    if "iteration_count" in data:
        config.iteration_count = int(data["iteration_count"])

    if "output_path" in data:
        config.output_path = str(data["output_path"])

    if "threads" in data:
        config.threads = int(data["threads"])

    if "seed" in data:
        config.seed = float(data["seed"])

    if "gamma_correction" in data:
        config.gamma_correction = bool(data["gamma_correction"])

    if "gamma" in data:
        config.gamma = float(data["gamma"])

    if "symmetry_level" in data:
        config.symmetry_level = int(data["symmetry_level"])


def _apply_global_affine(config: Config, data: JsonMapping) -> None:
    affine = _as_dict(data.get("affine_params"))
    if affine is None:
        return

    config.affine_params = AffineParams(
        a=float(affine.get("a", config.affine_params.a)),
        b=float(affine.get("b", config.affine_params.b)),
        c=float(affine.get("c", config.affine_params.c)),
        d=float(affine.get("d", config.affine_params.d)),
        e=float(affine.get("e", config.affine_params.e)),
        f=float(affine.get("f", config.affine_params.f)),
    )


def _parse_affine_params_dict(affine_dict: JsonMapping) -> AffineParams:
    return AffineParams(
        a=float(affine_dict.get("a", 1.0)),
        b=float(affine_dict.get("b", 0.0)),
        c=float(affine_dict.get("c", 0.0)),
        d=float(affine_dict.get("d", 0.0)),
        e=float(affine_dict.get("e", 1.0)),
        f=float(affine_dict.get("f", 0.0)),
    )


def _apply_functions_from_json(config: Config, data: JsonMapping) -> None:
    funcs = _as_list(data.get("functions"))
    if funcs is None:
        return

    parsed: list[FunctionConfig] = []

    for item in funcs:
        obj = _as_dict(item)
        if obj is None:
            continue

        name = obj.get("name")
        weight = obj.get("weight")
        if name is None or weight is None:
            continue

        affine_params: AffineParams | None = None
        affine_dict = _as_dict(obj.get("affine_params"))
        if affine_dict is not None:
            affine_params = _parse_affine_params_dict(affine_dict)

        parsed.append(
            FunctionConfig(
                name=str(name),
                weight=float(weight),
                affine_params=affine_params,
            )
        )

    if parsed:
        config.functions = parsed


def _apply_json_to_config(config: Config, data: JsonMapping) -> None:
    _apply_size(config, data)
    _apply_scalar_fields(config, data)
    _apply_global_affine(config, data)
    _apply_functions_from_json(config, data)


def _apply_cli_to_config(config: Config, cli_args: "argparse.Namespace") -> None:
    """Apply CLI overrides to config.

    Order:
    1) size (nested)
    2) scalar fields
    3) flags and parsed structures
    """
    if cli_args.width is not None:
        config.size.width = cli_args.width
    if cli_args.height is not None:
        config.size.height = cli_args.height

    overrides: dict[str, object] = {
        "iteration_count": cli_args.iteration_count,
        "output_path": cli_args.output_path,
        "threads": cli_args.threads,
        "seed": cli_args.seed,
        "gamma": cli_args.gamma,
        "symmetry_level": cli_args.symmetry_level,
    }
    for attr, value in overrides.items():
        if value is not None:
            setattr(config, attr, value)

    if cli_args.gamma_correction:
        config.gamma_correction = True
    if cli_args.affine_params:
        config.affine_params = _parse_affine_params(cli_args.affine_params)
    if cli_args.functions:
        config.functions = _parse_functions(cli_args.functions)


def build_config(cli_args: "argparse.Namespace") -> Config:
    """Merge defaults, JSON config (if provided) and CLI into final Config."""
    config = Config(
        size=SizeConfig(),
        iteration_count=DEFAULT_ITERATION_COUNT,
        output_path=DEFAULT_OUTPUT_PATH,
        threads=DEFAULT_THREADS,
        seed=DEFAULT_SEED,
        functions=[FunctionConfig(name=DEFAULT_FUNCTION, weight=1.0)],
        affine_params=AffineParams(),
        gamma=DEFAULT_GAMMA,
        symmetry_level=DEFAULT_SYMMETRY_LEVEL,
    )

    if cli_args.config:
        json_data = load_json_config(cli_args.config)
        _apply_json_to_config(config, json_data)

    _apply_cli_to_config(config, cli_args)
    return config


def validate_config(config: Config) -> None:
    """Validate configuration values."""
    if config.size.width <= 0 or config.size.height <= 0:
        msg = "Width and height must be positive integers"
        _raise_config(msg)

    if config.iteration_count <= 0:
        msg = "Iteration count must be a positive integer"
        _raise_config(msg)

    if config.threads <= 0:
        msg = "Threads must be a positive integer"
        _raise_config(msg)

    if not config.functions:
        msg = "At least one transform function must be configured"
        _raise_config(msg)

    if all(f.weight == 0.0 for f in config.functions):
        msg = "At least one function must have a non-zero weight"
        _raise_config(msg)

    if config.gamma <= 0:
        msg = "Gamma must be positive"
        _raise_config(msg)

    if config.symmetry_level < 1:
        msg = "Symmetry level must be >= 1"
        _raise_config(msg)

    # Local import to avoid circular dependency with transforms module.
    from .transforms import compile_variations

    try:
        # Ensure that all function names are known and affine params are valid.
        compile_variations(config.functions, config.affine_params)
    except KeyError as exc:
        raise ConfigError(str(exc)) from exc
