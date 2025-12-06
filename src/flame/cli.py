import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fractal flame generator.",
        add_help=False,
    )

    parser.add_argument("--help", action="help", help="Show help message and exit")

    parser.add_argument(
        "-w",
        "--width",
        type=int,
        help="Image width (default 1920)",
    )
    parser.add_argument(
        "-h",
        "--height",
        type=int,
        help="Image height (default 1080)",
    )

    parser.add_argument(
        "--seed",
        type=float,
        help="Initial random seed (default 5.1234)",
    )
    parser.add_argument(
        "-i",
        "--iteration-count",
        type=int,
        help="Number of iterations (default 2500)",
    )
    parser.add_argument(
        "-o",
        "--output-path",
        type=str,
        help="Output PNG file path (default result.png)",
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        help="Number of threads (default 1)",
    )
    parser.add_argument(
        "-ap",
        "--affine-params",
        type=str,
        help="Affine params in format a,b,c,d,e,f",
    )
    parser.add_argument(
        "-f",
        "--functions",
        type=str,
        help="Transform functions in format name:weight,name:weight",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON config file",
    )

    parser.add_argument(
        "-g",
        "--gamma-correction",
        action="store_true",
        help="Enable gamma correction",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        help="Gamma value for correction (default 2.2)",
    )
    parser.add_argument(
        "-s",
        "--symmetry-level",
        type=int,
        help="Symmetry level (N >= 1, default 1)",
    )

    return parser.parse_args()
