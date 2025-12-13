import logging
import sys
from pathlib import Path

from .cli import parse_args
from .config import ConfigError, build_config, validate_config
from .mp_runner import generate_flame
from .render import render_image


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    return logging.getLogger("fractal_flame")


def main() -> int:
    logger = setup_logging()

    try:
        args = parse_args()
        config = build_config(args)
        validate_config(config)

        logger.info(
            "Generating fractal flame %dx%d, threads=%d, output=%s, iterations=%d",
            config.size.width,
            config.size.height,
            config.threads,
            config.output_path,
            config.iteration_count,
        )

        histogram, colors = generate_flame(config)
        image = render_image(config, histogram, colors)

        output_path = Path(config.output_path)
        if output_path.suffix.lower() != ".png":
            logger.warning(
                "Output file does not have .png extension, forcing .png extension"
            )
            output_path = output_path.with_suffix(".png")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="PNG")
        logger.info("Image saved to %s", output_path)

        return 0
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        return 1
    except Exception as exc:
        logger.exception("Unhandled error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
