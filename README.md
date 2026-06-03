# Fractal Flame Generator

[![CI](https://github.com/tigdav/fractal-flame/actions/workflows/ci.yml/badge.svg)](https://github.com/tigdav/fractal-flame/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)

A Python implementation of a fractal flame image generator based on the Chaos Game approach.

The project supports single-threaded and multi-process rendering modes, configurable transformations,
and multiple input methods (CLI arguments and JSON configuration files). It focuses on correctness,
reproducibility, and code quality rather than advanced post-processing techniques.

---

## Features

- Fractal flame generation using the Chaos Game algorithm
- Color blending based on transformation weights
- Support for multiple non-linear transformations:
    - swirl
    - horseshoe
    - spherical
    - sinusoidal
    - linear
- Single-threaded and multi-process rendering modes
- Configurable image size, iteration count, and output path
- Output format: PNG image (RGB, 8-bit per channel)
- Optional gamma correction
- Optional rotational symmetry
- Flexible affine transformation configuration (global or per-function)
- CLI-based and JSON-based configuration
- Input validation and informative error messages
- Progress logging during rendering

---

## Installation

### Requirements

- Python 3.11+
- Poetry

### Setup

```bash
git clone https://github.com/tigdav/fractal-flame.git
cd fractal-flame
poetry install
```

---

## Usage

### Command-line usage

Basic example:

```bash
poetry run python -m flame -i 500000 -f swirl:1.0,horseshoe:0.8 -t 4
```

Reproducible example with a fixed seed:

```bash
poetry run python -m flame --seed 32.123531 -i 5000 -f swirl:1.0,horseshoe:0.8 -t 2
```

#### Affine parameters from CLI

The `-ap / --affine-params` option supports **one or multiple affine transformation sets**.

**Single affine set (global)**  
Applied to all transformation functions:

```bash
-ap 1.0,0.0,0.0,0.0,1.0,0.0
```

**Multiple affine sets (per-function)**  
Affine sets are separated by `/` and must match the number of functions passed via `-f`:

```bash
-f swirl:1.0,horseshoe:0.8 -ap 1.0,0.0,0.0,0.0,1.0,0.0/0.3,1.0,-0.2,0.4,1.0,1.0
```

In this case, the first affine set is applied to `swirl`, and the second one to `horseshoe`.

Available CLI options include:

- `-w`, `--width` — output image width
- `-h`, `--height` — output image height
- `--seed` — random seed (default 5)
- `-i`, `--iteration-count` — number of iterations
- `-o`, `--output-path` — output PNG file path
- `-t`, `--threads` — number of worker processes (default 1)
- `-f`, `--functions` — transformation functions and weights
- `-ap`, `--affine-params` — affine transformation parameters (single or multiple)
- `-g`, `--gamma-correction` — enable gamma correction
- `--gamma` — gamma value
- `-s`, `--symmetry-level` — rotational symmetry level
- `--config` — JSON configuration file

Run with `--help` to see the full list of options.

---

### Configuration file usage

All parameters can be provided using a JSON configuration file:

```bash
poetry run python -m flame --config configs/pretty_flame.json
```

#### Affine parameters in JSON

Affine transformations can be defined in multiple ways:

**Global affine transformation**

```json
{
  "affine_params": {
    "a": 1.0,
    "b": 0.0,
    "c": 0.0,
    "d": 0.0,
    "e": 1.0,
    "f": 0.0
  }
}
```

**Multiple affine transformations (per-function)**

```json
{
  "affine_params": [
    {
      "a": 1.0,
      "b": 0.0,
      "c": 0.0,
      "d": 0.0,
      "e": 1.0,
      "f": 0.0
    },
    {
      "a": 0.3,
      "b": 1.0,
      "c": -0.2,
      "d": 0.4,
      "e": 1.0,
      "f": 1.0
    }
  ]
}
```

If multiple affine sets are provided, their count must match the number of configured functions.

Affine parameters can also be specified directly inside individual function definitions.
Per-function affine configuration has higher priority than global affine settings.

When multiple sources are used, the following priority applies:

1. CLI arguments
2. JSON configuration file
3. Default values

---

## Examples

Example images generated with predefined configurations are available in the `examples/` directory.

See [`examples/README.md`](examples/README.md) for:

- generated images
- corresponding configuration files
- reproduction commands

---

## Performance benchmarks

The project includes benchmark scripts comparing single-threaded and multi-process rendering.

Benchmark scripts and results are available in the `benchmarks/` directory.

See [`benchmarks/README.md`](benchmarks/README.md) for details.

---

## Project structure

```
src/flame/        Core implementation
configs/          Example configuration files
examples/         Generated images and usage examples
benchmarks/       Performance measurement scripts
tests/            Unit and integration tests
```

---

## Testing

The project includes unit tests covering core functionality:

- transformation correctness
- configuration parsing
- rendering pipeline
- multi-process execution

Tests can be run with:

```bash
poetry run pytest
```

### Test coverage

Test coverage is measured using `pytest-cov`.

| Module           | Coverage |
|------------------|----------|
| flame.__main__   | 97%      |
| flame.affine     | 100%     |
| flame.cli        | 100%     |
| flame.config     | 94%      |
| flame.core       | 98%      |
| flame.mp_runner  | 100%     |
| flame.render     | 95%      |
| flame.transforms | 100%     |
| **Total**        | **97%**  |

Coverage was measured using:

```bash
poetry run pytest --cov=src/flame --cov-report=term
```

---

## Notes

- Visual output may vary slightly depending on platform and floating-point behavior.
- The implementation does not include advanced post-processing techniques
  (e.g. log-density normalization or image filtering).
