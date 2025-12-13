import argparse
import json
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    """Raised when configuration is invalid."""


@dataclass
class SizeConfig:
    """Image size configuration."""

    width: int = 1920
    height: int = 1080


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
    gamma: float = 2.2
    symmetry_level: int = 1


def load_json_config(path: str) -> dict:
    """Load JSON configuration file into plain dictionary.

    Args:
        path: Path to JSON config file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        ConfigError: If file cannot be read or parsed.

    """
    try:
        config_path = Path(path)
        if not config_path.exists():
            raise ConfigError(f"Config file not found: {path}")

        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ConfigError("JSON config root must be an object")

        return data
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Failed to parse JSON config: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Failed to read config file: {exc}") from exc


def _parse_affine_params(value: str) -> AffineParams:
    parts = value.split(",")
    if len(parts) != 6:
        raise ConfigError(
            "Affine params must have 6 comma-separated values a,b,c,d,e,f"
        )

    try:
        a, b, c, d, e, f = (float(p.strip()) for p in parts)
    except ValueError as exc:
        raise ConfigError(f"Affine params must be floats: {value}") from exc

    return AffineParams(a=a, b=b, c=c, d=d, e=e, f=f)


def _parse_functions(value: str) -> list[FunctionConfig]:
    functions: list[FunctionConfig] = []

    for item in value.split(","):
        item = item.strip()
        if not item:
            continue

        if ":" not in item:
            raise ConfigError(f"Function spec must be name:weight, got: {item}")

        name, weight_str = item.split(":", 1)
        name = name.strip()
        try:
            weight = float(weight_str.strip())
        except ValueError as exc:
            raise ConfigError(
                f"Invalid weight for function '{name}': {weight_str}"
            ) from exc

        functions.append(FunctionConfig(name=name, weight=weight))

    if not functions:
        raise ConfigError("At least one function must be specified")

    return functions


def _apply_json_to_config(config: Config, data: dict) -> None:
    size = data.get("size")
    if isinstance(size, dict):
        if "width" in size:
            config.size.width = int(size["width"])
        if "height" in size:
            config.size.height = int(size["height"])

    if "iteration_count" in data:
        config.iteration_count = int(data["iteration_count"])

    if "output_path" in data:
        config.output_path = str(data["output_path"])

    if "threads" in data:
        config.threads = int(data["threads"])

    if "seed" in data:
        config.seed = float(data["seed"])

    affine = data.get("affine_params")
    if isinstance(affine, dict):
        config.affine_params = AffineParams(
            a=float(affine.get("a", config.affine_params.a)),
            b=float(affine.get("b", config.affine_params.b)),
            c=float(affine.get("c", config.affine_params.c)),
            d=float(affine.get("d", config.affine_params.d)),
            e=float(affine.get("e", config.affine_params.e)),
            f=float(affine.get("f", config.affine_params.f)),
        )

    funcs = data.get("functions")
    if isinstance(funcs, list):
        parsed: list[FunctionConfig] = []
        for item in funcs:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            weight = item.get("weight")
            if name is None or weight is None:
                continue

            affine_params_dict = item.get("affine_params")
            affine_params: AffineParams | None = None
            if isinstance(affine_params_dict, dict):
                affine_params = AffineParams(
                    a=float(affine_params_dict.get("a", 1.0)),
                    b=float(affine_params_dict.get("b", 0.0)),
                    c=float(affine_params_dict.get("c", 0.0)),
                    d=float(affine_params_dict.get("d", 0.0)),
                    e=float(affine_params_dict.get("e", 1.0)),
                    f=float(affine_params_dict.get("f", 0.0)),
                )

            parsed.append(
                FunctionConfig(
                    name=str(name),
                    weight=float(weight),
                    affine_params=affine_params,
                )
            )
        if parsed:
            config.functions = parsed

    if "gamma_correction" in data:
        config.gamma_correction = bool(data["gamma_correction"])

    if "gamma" in data:
        config.gamma = float(data["gamma"])

    if "symmetry_level" in data:
        config.symmetry_level = int(data["symmetry_level"])


def build_config(cli_args: argparse.Namespace) -> Config:
    """Merge defaults, JSON config (if provided) and CLI into final Config."""
    config = Config(
        size=SizeConfig(),
        iteration_count=2500,
        output_path="result.png",
        threads=1,
        seed=5.1234,
        functions=[FunctionConfig(name="swirl", weight=1.0)],
        affine_params=AffineParams(),
    )

    if cli_args.config:
        json_data = load_json_config(cli_args.config)
        _apply_json_to_config(config, json_data)

    if cli_args.width is not None:
        config.size.width = cli_args.width

    if cli_args.height is not None:
        config.size.height = cli_args.height

    if cli_args.iteration_count is not None:
        config.iteration_count = cli_args.iteration_count

    if cli_args.output_path is not None:
        config.output_path = cli_args.output_path

    if cli_args.threads is not None:
        config.threads = cli_args.threads

    if cli_args.seed is not None:
        config.seed = cli_args.seed

    if cli_args.affine_params:
        config.affine_params = _parse_affine_params(cli_args.affine_params)

    if cli_args.functions:
        config.functions = _parse_functions(cli_args.functions)

    if cli_args.gamma_correction:
        config.gamma_correction = True

    if cli_args.gamma is not None:
        config.gamma = cli_args.gamma

    if cli_args.symmetry_level is not None:
        config.symmetry_level = cli_args.symmetry_level

    return config


def validate_config(config: Config) -> None:
    """Validate configuration values.

    Args:
        config: Configuration object to validate.

    Raises:
        ConfigError: If any configuration field is invalid or inconsistent.

    """
    if config.size.width <= 0 or config.size.height <= 0:
        raise ConfigError("Width and height must be positive integers")

    if config.iteration_count <= 0:
        raise ConfigError("Iteration count must be positive integer")

    if config.threads <= 0:
        raise ConfigError("Threads must be positive integer")

    if not config.functions:
        raise ConfigError("At least one transform function must be configured")

    if all(f.weight == 0.0 for f in config.functions):
        raise ConfigError("At least one function must have non-zero weight")

    if config.gamma <= 0:
        raise ConfigError("Gamma must be positive")

    if config.symmetry_level < 1:
        raise ConfigError("Symmetry level must be >= 1")

    # Local import to avoid circular dependency with transforms module.
    from .transforms import compile_variations

    try:
        # Ensure that all function names are known and affine params are valid.
        compile_variations(config.functions, config.affine_params)
    except KeyError as exc:
        raise ConfigError(str(exc)) from exc
