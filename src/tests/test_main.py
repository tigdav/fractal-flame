import logging
from types import SimpleNamespace

import numpy as np
from PIL import Image

import flame.__main__ as main_module
from flame.config import AffineParams, Config, ConfigError, FunctionConfig, SizeConfig


def _make_config(output_path: str) -> Config:
    return Config(
        size=SizeConfig(width=4, height=3),
        iteration_count=10,
        output_path=output_path,
        threads=1,
        seed=5.0,
        functions=[FunctionConfig(name="swirl", weight=1.0)],
        affine_params=AffineParams(),
        gamma_correction=False,
        gamma=2.2,
        symmetry_level=1,
    )


def test_main_creates_png_and_returns_zero(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.INFO)

    # make CLI parser return anything, it will be passed into build_config
    monkeypatch.setattr(main_module, "parse_args", lambda: SimpleNamespace(dummy=True))

    # config with non-png extension to test forcing .png suffix
    raw_output = tmp_path / "image.jpg"
    config = _make_config(str(raw_output))

    def fake_build_config(args):
        return config

    def fake_validate_config(cfg):
        assert cfg is config

    fake_hist = np.ones((3, 4), dtype=np.float64)
    fake_colors = np.zeros((3, 4, 3), dtype=np.float64)

    def fake_generate_flame(cfg):
        assert cfg is config
        return fake_hist, fake_colors

    def fake_render_image(cfg, hist, colors):
        assert cfg is config
        assert hist is fake_hist
        assert colors is fake_colors
        return Image.new("RGB", (cfg.size.width, cfg.size.height))

    monkeypatch.setattr(main_module, "build_config", fake_build_config)
    monkeypatch.setattr(main_module, "validate_config", fake_validate_config)
    monkeypatch.setattr(main_module, "generate_flame", fake_generate_flame)
    monkeypatch.setattr(main_module, "render_image", fake_render_image)

    exit_code = main_module.main()
    assert exit_code == 0

    files = list(tmp_path.iterdir())
    assert len(files) == 1
    out = files[0]
    assert out.suffix == ".png"
    assert out.is_file()

    # basic sanity check that file is a PNG
    with Image.open(out) as img:
        assert img.mode == "RGB"
        assert img.size == (config.size.width, config.size.height)


def test_main_returns_one_on_config_error(monkeypatch, caplog):
    caplog.set_level(logging.ERROR)

    monkeypatch.setattr(main_module, "parse_args", lambda: SimpleNamespace(dummy=True))

    def fake_build_config(args):
        msg = "bad config"
        raise ConfigError(msg)

    monkeypatch.setattr(main_module, "build_config", fake_build_config)

    exit_code = main_module.main()
    assert exit_code == 1

    assert any("Configuration error" in rec.message for rec in caplog.records)


def test_main_returns_one_on_unhandled_exception(monkeypatch, caplog):
    caplog.set_level(logging.ERROR)

    monkeypatch.setattr(main_module, "parse_args", lambda: SimpleNamespace(dummy=True))

    def fake_build_config(args):
        msg = "boom"
        raise RuntimeError(msg)

    monkeypatch.setattr(main_module, "build_config", fake_build_config)

    exit_code = main_module.main()
    assert exit_code == 1

    assert any("Unhandled error" in rec.message for rec in caplog.records)
