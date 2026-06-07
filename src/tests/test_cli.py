import sys

import pytest

from flame.cli import parse_args


def test_parse_args_defaults(monkeypatch):
    """No CLI args: all optional fields should be None/False."""
    monkeypatch.setattr(sys, "argv", ["prog"])

    args = parse_args()

    assert args.width is None
    assert args.height is None
    assert args.seed is None
    assert args.iteration_count is None
    assert args.output_path is None
    assert args.workers is None
    assert args.affine_params is None
    assert args.functions is None
    assert args.config is None
    assert args.gamma_correction is False
    assert args.gamma is None
    assert args.symmetry_level is None


def test_parse_args_full_option_set(monkeypatch):
    """Typical CLI call with most options set."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prog",
            "-w",
            "800",
            "-h",
            "600",
            "--seed",
            "1.23",
            "-i",
            "10000",
            "-o",
            "out.png",
            "--workers",
            "4",
            "-ap",
            "0.1,0.2,0.3,0.4,0.5,0.6",
            "-f",
            "swirl:1.0,horseshoe:0.8",
            "--config",
            "config.json",
            "-g",
            "--gamma",
            "1.7",
            "-s",
            "3",
        ],
    )

    args = parse_args()

    assert args.width == 800
    assert args.height == 600
    assert args.seed == pytest.approx(1.23)
    assert args.iteration_count == 10000
    assert args.output_path == "out.png"
    assert args.workers == 4
    assert args.affine_params == "0.1,0.2,0.3,0.4,0.5,0.6"
    assert args.functions == "swirl:1.0,horseshoe:0.8"
    assert args.config == "config.json"
    assert args.gamma_correction is True
    assert args.gamma == pytest.approx(1.7)
    assert args.symmetry_level == 3


def test_parse_args_help_exits(monkeypatch):
    """--help should trigger SystemExit with code 0."""
    monkeypatch.setattr(sys, "argv", ["prog", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        parse_args()

    assert exc_info.value.code == 0
